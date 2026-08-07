import json
from datetime import datetime
from pathlib import Path


def _format_datetime(timestamp):
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


def _format_size(size):
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024


def _markdown_cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _inventory_records(value):
    """Yield copied-file records embedded in an inventory JSON structure."""
    if isinstance(value, dict):
        if "backup" in value and isinstance(value["backup"], str):
            yield value
        for child in value.values():
            yield from _inventory_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from _inventory_records(child)


def _load_inventories(backup_path):
    inventories = {}
    inventory_dir = backup_path / "inventory"
    if not inventory_dir.is_dir():
        return inventories
    for inventory_path in sorted(inventory_dir.glob("*.json")):
        try:
            inventories[inventory_path.stem] = json.loads(
                inventory_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as error:
            inventories[inventory_path.stem] = {"error": str(error)}
    return inventories


def _file_rows(backup_path):
    rows = []
    for path in sorted(backup_path.rglob("*")):
        if not path.is_file() or path.name == "checksums.json":
            continue
        try:
            stat = path.stat()
            rows.append(
                {
                    "path": str(path.relative_to(backup_path)),
                    "size": _format_size(stat.st_size),
                    "modified": _format_datetime(stat.st_mtime),
                }
            )
        except OSError as error:
            rows.append(
                {
                    "path": str(path.relative_to(backup_path)),
                    "size": "n/d",
                    "modified": f"errore: {error}",
                }
            )
    return rows


def _backup_totals(backup_path):
    file_count = 0
    total_size = 0
    for path in backup_path.rglob("*"):
        if path.is_file() and path.name != "checksums.json":
            try:
                file_count += 1
                total_size += path.stat().st_size
            except OSError:
                pass
    return file_count, total_size


def create_backup_summary(backup_path, manifest, archive_name, summary_path):
    """Create a non-sensitive, terminal-friendly text summary."""
    backup_path = Path(backup_path)
    summary_path = Path(summary_path)
    modules = manifest.get("modules", {})
    file_count, total_size = _backup_totals(backup_path)
    failed = [name for name, result in modules.items() if result.get("status") != "success"]
    successful = sum(result.get("status") == "success" for result in modules.values())

    module_label = "Module"
    result_label = "Result"
    artifact_label = "Artifacts"
    module_width = max(
        [len(module_label)] + [len(str(name)) for name in modules]
    )
    result_width = max(
        [len(result_label)]
        + [len(str(result.get("status", "n/a"))) for result in modules.values()]
    )
    lines = [
        "MAC RESTORE - BACKUP SUMMARY",
        "=" * 60,
        "",
        f"Archive          : {archive_name}",
        f"Created          : {manifest.get('created', 'n/a')}",
        f"Modules completed: {successful}/{len(modules)}",
        f"Files stored     : {file_count}",
        f"Total stored size: {_format_size(total_size)}",
        f"Overall result   : {'WARNING - one or more modules failed' if failed else 'OK - all selected modules completed'}",
        "",
        "MODULE RESULTS",
        "-" * 60,
        f"{module_label:<{module_width}}  {result_label:<{result_width}}  {artifact_label}",
        f"{'-' * module_width}  {'-' * result_width}  {'-' * len(artifact_label)}",
    ]
    for name, result in modules.items():
        lines.append(
            f"{str(name):<{module_width}}  "
            f"{str(result.get('status', 'n/a')):<{result_width}}  "
            f"{len(result.get('artifacts', []))}"
        )
    if failed:
        lines.extend(["", "Modules requiring attention: " + ", ".join(failed) + "."])
    lines.extend(
        [
            "",
            "This summary intentionally excludes source paths, file names, inventory",
            "contents and credentials.",
            "Use Mac Restore > Restore > View backup details to inspect the complete",
            "report after entering the backup password.",
            "",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def create_backup_report(backup_path, manifest, report_name="backup_report.md"):
    """Create a human-readable report inside a plaintext staging backup."""
    backup_path = Path(backup_path)
    inventories = _load_inventories(backup_path)
    modules = manifest.get("modules", {})
    rows = _file_rows(backup_path)
    copied_records = []

    for module_name, inventory in inventories.items():
        data = inventory.get("data", inventory)
        for record in _inventory_records(data):
            copied_records.append(
                {
                    "module": module_name,
                    "source": record.get("source", "n/d"),
                    "backup": record["backup"],
                    "restore_to": record.get("restore_to", "n/d"),
                }
            )

    lines = [
        "# Mac Restore — Detailed Backup Report",
        "",
        f"- **Created:** {manifest.get('created', 'n/a')}",
        f"- **Computer:** {manifest.get('hostname', 'n/a')}",
        f"- **Platform:** {manifest.get('platform', 'n/a')}",
        f"- **Python:** {manifest.get('python', 'n/a')}",
        "- **Encryption:** AES-256-GCM",
        "",
        "## Module summary",
        "",
        "| Module | Result | Registered artifacts | Details |",
        "|---|---|---:|---|",
    ]

    for name, result in modules.items():
        status = result.get("status", "n/d")
        details = result.get("error", "OK")
        artifacts = len(result.get("artifacts", []))
        lines.append(
            f"| {_markdown_cell(name)} | **{_markdown_cell(status)}** | "
            f"{artifacts} | {_markdown_cell(details)} |"
        )

    failed = [name for name, result in modules.items() if result.get("status") != "success"]
    lines.extend(
        [
            "",
            f"**Overall result:** {'WARNING — one or more modules failed' if failed else 'OK — all modules completed successfully'}.",
        ]
    )
    if failed:
        lines.append(f"Modules requiring attention: {', '.join(failed)}.")

    lines.extend(["", "## Files with recorded source", ""])
    if copied_records:
        lines.extend(
            [
                "| Module | Source | In backup | Restore destination |",
                "|---|---|---|---|",
            ]
        )
        for record in copied_records:
            lines.append(
                "| "
                + " | ".join(
                    _markdown_cell(record[key])
                    for key in ("module", "source", "backup", "restore_to")
                )
                + " |"
            )
    else:
        lines.append("No file source/destination records are available in the inventories.")

    lines.extend(
        [
            "",
            "## Files in the archive",
            "",
            "The timestamp is the modification time of the file in the backup. For "
            "files copied with `copy2`/`copytree`, it matches the original modification "
            "time; generated files show their generation time.",
            "",
            "| File | Size | Modified |",
            "|---|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {_markdown_cell(row['path'])} | {row['size']} | {row['modified']} |"
        )

    lines.extend(["", "## Detailed inventories", ""])
    for name, inventory in inventories.items():
        lines.extend(
            [
                f"### {name}",
                "",
                "```json",
                json.dumps(inventory, indent=2, ensure_ascii=False, default=str),
                "```",
                "",
            ]
        )

    report_path = backup_path / report_name
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def create_restore_report(report_path, backup_name, dry_run, module_results):
    """Write a plain-text restore result report for both dry-run and live modes."""
    report_path = Path(report_path)
    successful = sum(item["status"] == "success" for item in module_results)
    failed = sum(item["status"] == "failed" for item in module_results)
    skipped = sum(item["status"] == "skipped" for item in module_results)
    mode = "DRY-RUN (no files changed)" if dry_run else "LIVE EXECUTION"
    module_width = max([len("Module")] + [len(item["name"]) for item in module_results])
    status_width = max([len("Status")] + [len(item["status"]) for item in module_results])

    lines = [
        "MAC RESTORE - RESTORE REPORT",
        "=" * 72,
        "",
        f"Backup: {backup_name}",
        f"Mode: {mode}",
        f"Created: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Modules completed: {successful}",
        f"Modules failed: {failed}",
        f"Modules skipped: {skipped}",
        "",
        "MODULE RESULTS",
        "-" * 72,
        f"{'Module':<{module_width}}  {'Status':<{status_width}}  Details",
        f"{'-' * module_width}  {'-' * status_width}  --------",
    ]
    for item in module_results:
        lines.append(
            f"{item['name']:<{module_width}}  {item['status']:<{status_width}}  "
            f"{item.get('error', 'Completed')}"
        )
        output = item.get("output", "").strip()
        if output:
            lines.append("  Actions:")
            lines.extend(f"    {line}" for line in output.splitlines())
    lines.extend(
        [
            "",
            "END OF RESTORE REPORT",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def print_verification(result):

    if result["valid"]:

        print()
        print("[OK] Backup is valid")

    else:

        print()
        print("[ERROR] Backup is invalid")


    print()


    if result.get("error"):
        print("Error:", result["error"])
        return

    for item in result.get("files", []):

        symbol = "[OK]"

        if item["status"] != "ok":
            symbol = "[ERROR]"


        print(
            symbol,
            item["file"],
            "-",
            item["status"]
        )
