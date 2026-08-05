"""Restore guidance and validation for VMware Fusion virtual machines."""

import json
import os
from pathlib import Path


PLUGIN = {
    "name": "vmware",
    "description": "Verify and guide VMware Fusion VM restoration",
}


def _load_inventory(context):
    inventory_file = context.inventory_dir / "vmware.json"
    if not inventory_file.exists():
        return None
    try:
        return json.loads(inventory_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"  [ERROR] Unable to read VMware inventory: {error}")
        return None


def _current_status(vm):
    path = Path(vm.get("path", "")).expanduser()
    return {
        "path": str(path),
        "exists": path.is_dir(),
        "readable": os.access(path, os.R_OK) if path.exists() else False,
    }


def _write_report(destination, machines):
    lines = [
        "# VMware Fusion - restore",
        "",
        "macRestore does not copy virtual disks. Reinstall VMware Fusion,",
        "connect the external drive and open the `.vmwarevm` bundle listed below.",
        "",
    ]
    for machine in machines:
        status = _current_status(machine)
        lines.extend(
            [
                f"## {machine.get('name', 'Unnamed VM')}",
                f"- Recorded path: `{machine.get('path', '')}`",
                f"- Present now: `{'yes' if status['exists'] else 'no'}`",
                f"- Readable now: `{'yes' if status['readable'] else 'no'}`",
                "- Action: open the `.vmwarevm` bundle from VMware Fusion.",
                "",
            ]
        )
    destination.write_text("\n".join(lines), encoding="utf-8")


def restore(context):
    payload = _load_inventory(context)
    if not payload:
        print("  [SKIP] No VMware inventory found, skipping.")
        return

    machines = payload.get("data", {}).get("virtual_machines", [])
    if not machines:
        print("  [SKIP] No VMware VMs recorded in the backup.")
        return

    for machine in machines:
        status = _current_status(machine)
        label = machine.get("name", "Unnamed VM")
        if status["exists"] and status["readable"]:
            print(f"  [OK] {label}: bundle found and readable -> {status['path']}")
        else:
            print(f"  [WARNING] {label}: bundle not found at the recorded path -> {status['path']}")

    report = Path.home() / "Desktop" / "VMware_Fusion_Restore.md"
    if context.dry_run:
        print(f"  [DRY-RUN] Would create restore instructions at {report}")
        print("  [NOTE] Reinstall VMware Fusion and open the .vmwarevm bundle from the external drive.")
        return

    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        _write_report(report, machines)
        print(f"  [OK] VMware instructions saved to: {report}")
        print("  [NOTE] Open the .vmwarevm bundle manually with VMware Fusion.")
    except OSError as error:
        print(f"  [ERROR] Error creating the VMware report: {error}")
