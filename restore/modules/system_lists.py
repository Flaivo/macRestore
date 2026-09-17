import shutil
import json
import shlex
from pathlib import Path

from shared.application_sources import application_download_url, is_macos_component

PLUGIN = {
    "name": "system_lists",
    "description": "Extract Brewfile, application lists and disk report to the Desktop"
}

MYSQL_DOWNLOADS = {
    "MySQL Community Server (macOS ARM64 / Apple Silicon)": "https://dev.mysql.com/downloads/mysql/",
    "MySQL Workbench (macOS)": "https://dev.mysql.com/downloads/workbench/",
}

PRINTER_DRIVER_SOURCES = {
    "xerox": (
        "Xerox Drivers & Downloads",
        "https://www.support.xerox.com/en-us",
    ),
    "zebra": (
        "Zebra Printers Support & Downloads",
        "https://www.zebra.com/us/en/support-downloads/printers.html",
    ),
    "canon": (
        "Canon Software & Drivers",
        "https://www.usa.canon.com/support/software-and-drivers",
    ),
}


def _markdown_cell(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def _write_application_downloads(app_dir, dest_dir):
    """Create a current-version list with curated official download pages."""
    inventory_file = app_dir.parent.parent / "inventory" / "applications.json"
    applications = []
    brew_casks = []
    if inventory_file.exists():
        try:
            payload = json.loads(inventory_file.read_text(encoding="utf-8"))
            data = payload.get("data", payload)
            applications = data.get("installed_apps", [])
            brew_casks = data.get("brew_casks", [])
        except (OSError, json.JSONDecodeError):
            pass

    lines = [
        "# Application download and reinstall sources",
        "",
        "Links point to vendor-maintained download pages, not version-specific files.",
        "Check the selected architecture and license before installing.",
        "",
        "## Database tools",
        "",
        "| Component | Recommended package | Official download page |",
        "|---|---|---|",
    ]
    for name, url in MYSQL_DOWNLOADS.items():
        lines.append(f"| {_markdown_cell(name)} | Latest release for the current macOS version | [{url}]({url}) |")

    lines.extend([
        "",
        "## Installed applications",
        "",
        "| Application | Backed-up version | Reinstall source |",
        "|---|---:|---|",
    ])
    for app in sorted(
        (item for item in applications if not is_macos_component(item.get("name", ""))),
        key=lambda item: item.get("name", "").lower(),
    ):
        name = app.get("name", "Unknown")
        version = app.get("version") or "unknown"
        url = application_download_url(name)
        if is_macos_component(name):
            source = "macOS component / App Store"
        elif url:
            source = f"[{url}]({url})"
        else:
            source = "Official source not yet catalogued; verify the vendor site"
        lines.append(f"| {_markdown_cell(name)} | {_markdown_cell(version)} | {source} |")

    if brew_casks:
        lines.extend(["", "## Homebrew casks", "", "These can be reinstalled with `brew bundle --file=Brewfile`.", ""])
        for cask in sorted(brew_casks):
            lines.append(f"- `{cask}`")

    lines.extend([
        "",
        "## Notes",
        "",
        "- The backed-up version is included only as a migration reference; install the latest compatible release.",
        "- MySQL Server and MySQL Workbench are separate packages and should both be installed when Workbench is required.",
        "- Applications installed through the Mac App Store may require the Apple Account used for the original purchase.",
        "- Review this list before installing applications and do not run untrusted installers.",
        "",
    ])
    output = dest_dir / "APPLICATION_DOWNLOADS.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def _write_application_install_lists(app_dir, dest_dir):
    """Write an install-only application list and retain the complete inventory separately."""
    inventory_file = app_dir.parent.parent / "inventory" / "applications.json"
    applications = []
    if inventory_file.exists():
        try:
            payload = json.loads(inventory_file.read_text(encoding="utf-8"))
            applications = payload.get("data", payload).get("installed_apps", [])
        except (OSError, json.JSONDecodeError):
            pass

    installable = [
        item for item in applications
        if not is_macos_component(item.get("name", ""))
    ]
    installable_lines = [
        "# Applications to reinstall",
        "",
        "macOS system applications are intentionally excluded because they are provided by macOS.",
        "",
    ]
    installable_lines.extend(
        f"{item.get('name', 'Unknown')} {item.get('version') or ''}".rstrip()
        for item in sorted(installable, key=lambda item: item.get("name", "").lower())
    )
    (dest_dir / "applications.txt").write_text("\n".join(installable_lines) + "\n", encoding="utf-8")

    full_source = app_dir / "applications.txt"
    if full_source.exists():
        shutil.copy2(full_source, dest_dir / "applications-full.txt")


def _write_printer_restore_files(backup_dir, dest_dir):
    """Create a reviewable CUPS inventory and an opt-in queue recreation script."""
    inventory_file = backup_dir / "inventory" / "system.json"
    printers = []
    default_printer = ""
    if inventory_file.exists():
        try:
            payload = json.loads(inventory_file.read_text(encoding="utf-8"))
            data = payload.get("data", payload)
            printer_data = data.get("printers", {})
            printers = printer_data.get("printers", [])
            default_printer = printer_data.get("default_printer", "")
        except (OSError, json.JSONDecodeError):
            pass

    if not printers:
        return None, None

    guide_lines = [
        "# Printers — restore notes",
        "",
        "The backup records CUPS queues and connection URIs; it does not copy macOS printer drivers.",
        "Install the correct driver/software from the printer manufacturer first, if required.",
        "Review the URIs and run `restore_printers.sh` only when the printers are reachable.",
        "The script may ask for the macOS administrator password because `lpadmin` changes CUPS.",
        "",
        f"Default printer: `{default_printer or 'not set'}`",
        "",
        "| # | Queue/model | Connection URI | Driver/download page | Previous status | Default |",
        "|---:|---|---|---|---|---|",
    ]
    script_lines = [
        "#!/bin/sh",
        "set -u",
        "",
        'printf "This will modify CUPS printer queues and may require administrator privileges. Continue? [y/N] "',
        "IFS= read -r ANSWER",
        'case "$ANSWER" in y|Y) ;; *) echo "Printer restore cancelled."; exit 0 ;; esac',
        "",
        'if ! command -v lpadmin >/dev/null 2>&1; then echo "lpadmin is not available on this macOS installation." >&2; exit 1; fi',
        'echo "Choose only the queues you want to recreate. Each selection shows its driver page first."',
        "",
        "while :; do",
        '  echo ""',
        '  echo "Available printer queues:"',
    ]
    valid_printers = []
    for printer in printers:
        name = str(printer.get("name", "")).strip()
        uri = str(printer.get("device_uri", "")).strip()
        if not name or not uri:
            continue
        # Do not reproduce credentials accidentally embedded in a printer URI.
        if "@" in uri and "://" in uri:
            scheme, rest = uri.split("://", 1)
            uri = f"{scheme}://{rest.rsplit('@', 1)[-1]}"
        valid_printers.append((printer, name, uri))

    for index, (printer, name, uri) in enumerate(valid_printers, 1):
        driver_name = "Generic / Apple AirPrint"
        driver_url = "https://support.apple.com/guide/mac-help/add-a-printer-mh14004/mac"
        search_text = f"{name} {uri} {printer.get('interface', '')} {printer.get('make_and_model', '')}".casefold()
        for manufacturer, (label, url) in PRINTER_DRIVER_SOURCES.items():
            if manufacturer in search_text:
                driver_name, driver_url = label, url
                break
        driver_display = f"[{driver_name}]({driver_url})"
        model = printer.get("make_and_model") or printer.get("interface") or name
        guide_lines.append(
            f"| {index} | {_markdown_cell(name)} / {_markdown_cell(model)} | `{_markdown_cell(uri)}` | "
            f"{driver_display} | {_markdown_cell(printer.get('status', 'unknown'))} | "
            f"{'yes' if printer.get('is_default') else 'no'} |"
        )

        script_lines.append(f"  echo {shlex.quote('  ' + str(index) + '. ' + name)}")

    script_lines.extend([
        '  echo "  0. Finish"',
        '  printf "Select a queue (one at a time): "',
        "  IFS= read -r CHOICE",
        '  [ "$CHOICE" = "0" ] && break',
    ])
    for index, (printer, name, uri) in enumerate(valid_printers, 1):
        driver_name = "Generic / Apple AirPrint"
        driver_url = "https://support.apple.com/guide/mac-help/add-a-printer-mh14004/mac"
        search_text = f"{name} {uri} {printer.get('interface', '')} {printer.get('make_and_model', '')}".casefold()
        for manufacturer, (label, url) in PRINTER_DRIVER_SOURCES.items():
            if manufacturer in search_text:
                driver_name, driver_url = label, url
                break
        script_lines.extend([
            f'  if [ "$CHOICE" = "{index}" ]; then',
            f"    PRINTER_NAME={shlex.quote(name)}",
            f"    PRINTER_URI={shlex.quote(uri)}",
            f"    DRIVER_NAME={shlex.quote(driver_name)}",
            f"    DRIVER_URL={shlex.quote(driver_url)}",
            "    echo \"\"",
            '    echo "Queue: $PRINTER_NAME"',
            '    echo "Driver/software page: $DRIVER_URL"',
            '    printf "Open this page in the browser now? [y/N] "',
            "    IFS= read -r OPEN_PAGE",
            '    case "$OPEN_PAGE" in y|Y) command -v open >/dev/null 2>&1 && open "$DRIVER_URL" || echo "Open the URL manually." ;; esac',
            '    printf "Install/check the driver, then press Enter to continue (or type s to skip this queue): "',
            "    IFS= read -r READY",
            '    [ "$READY" = "s" ] || [ "$READY" = "S" ] || sudo lpadmin -p "$PRINTER_NAME" -E -v "$PRINTER_URI" -m everywhere || echo "Could not recreate this queue; select its manufacturer driver manually."',
        ])
        if printer.get("is_default"):
            script_lines.append('    sudo lpadmin -d "$PRINTER_NAME"')
        script_lines.extend([
            "    continue",
            "  fi",
        ])
    script_lines.extend([
        '  echo "Invalid selection."',
        "done",
        'echo "Printer restore finished; verify with lpstat -p -d."',
    ])

    guide = dest_dir / "PRINTERS.md"
    guide.write_text("\n".join(guide_lines) + "\n", encoding="utf-8")
    script = dest_dir / "restore_printers.sh"
    script.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    script.chmod(0o700)
    return guide, script


def _write_terminal_install_commands(dest_dir):
    """Create an interactive command helper for Homebrew packages and casks."""
    script = dest_dir / "INSTALL_COMMANDS.sh"
    script.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "\n"
        'SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
        'BREW_BIN=${BREW_BIN:-$(command -v brew 2>/dev/null || true)}\n'
        'if [ -z "$BREW_BIN" ]; then\n'
        '  printf "Homebrew is not installed. Install it now from the official installer? [y/N] "\n'
        '  IFS= read -r ANSWER\n'
        '  case "$ANSWER" in\n'
        '    y|Y) /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" ;;\n'
        '    *) echo "Homebrew installation cancelled."; exit 1 ;;\n'
        '  esac\n'
        '  if [ -x /opt/homebrew/bin/brew ]; then\n'
        '    BREW_BIN=/opt/homebrew/bin/brew\n'
        '  elif [ -x /usr/local/bin/brew ]; then\n'
        '    BREW_BIN=/usr/local/bin/brew\n'
        '  else\n'
        '    echo "Homebrew was not found after installation." >&2\n'
        '    exit 1\n'
        '  fi\n'
        'fi\n'
        '"$BREW_BIN" bundle --file="$SCRIPT_DIR/Brewfile"\n'
        'echo "Homebrew packages and casks restored."\n',
        encoding="utf-8",
    )
    script.chmod(0o700)
    return script


def _package_entries(payload):
    """Extract package name/version pairs from npm or pnpm list output."""
    entries = []
    candidates = payload if isinstance(payload, list) else [payload]
    for item in candidates:
        if not isinstance(item, dict):
            continue
        dependencies = item.get("dependencies", {})
        if not isinstance(dependencies, dict):
            continue
        for name, details in dependencies.items():
            if isinstance(details, dict):
                version = details.get("version")
            else:
                version = None
            entries.append((name, version))
    return sorted(set(entries), key=lambda item: item[0].lower())


def _write_node_global_commands(dest_dir):
    """Create a best-effort npm/pnpm global package restore helper."""
    commands = [
        "#!/bin/sh",
        "set -eu",
        "",
        'SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)',
        'if ! command -v npm >/dev/null 2>&1; then echo "npm is not installed; install Node.js/NVM first."; exit 0; fi',
        "",
        'echo "Restoring npm global packages..."',
    ]
    npm_file = dest_dir / "npm-global.json"
    if npm_file.exists():
        try:
            for name, version in _package_entries(json.loads(npm_file.read_text(encoding="utf-8"))):
                spec = f"{name}@{version}" if version else name
                commands.append(f"npm install --global {shlex.quote(spec)}")
        except (OSError, json.JSONDecodeError):
            pass

    pnpm_file = dest_dir / "pnpm-global.json"
    if pnpm_file.exists():
        commands.extend([
            "",
            'if command -v pnpm >/dev/null 2>&1; then',
            '  echo "Restoring pnpm global packages..."',
        ])
        try:
            for name, version in _package_entries(json.loads(pnpm_file.read_text(encoding="utf-8"))):
                spec = f"{name}@{version}" if version else name
                commands.append(f"  pnpm add --global {shlex.quote(spec)}")
        except (OSError, json.JSONDecodeError):
            pass
        commands.extend([
            "else",
            '  echo "pnpm is not installed; npm global packages were still processed."',
            "fi",
        ])
    commands.append('echo "Node global package restore completed."')
    script = dest_dir / "restore_node_globals.sh"
    script.write_text("\n".join(commands) + "\n", encoding="utf-8")
    script.chmod(0o700)
    return script


def _write_ide_extension_commands(dest_dir):
    """Create a VS Code-compatible extension installation helper."""
    extension_file = dest_dir / "vscode_extensions.txt"
    if not extension_file.exists():
        return None
    script = dest_dir / "install_ide_extensions.sh"
    script.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "\n"
        'if ! command -v code >/dev/null 2>&1; then echo "VS Code CLI (code) is not installed or not on PATH."; exit 0; fi\n'
        'while IFS= read -r extension; do\n'
        '  [ -n "$extension" ] || continue\n'
        '  code --install-extension "$extension"\n'
        'done < "$(dirname -- "$0")/vscode_extensions.txt"\n'
        'echo "IDE extensions restored."\n',
        encoding="utf-8",
    )
    script.chmod(0o700)
    return script


def _write_bootstrap_commands(dest_dir):
    """Create the short orchestrator for the first post-install setup."""
    script = dest_dir / "BOOTSTRAP_MAC.sh"
    script.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "\n"
        'SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
        'run_optional() { if [ -x "$SCRIPT_DIR/$1" ]; then echo "==> Running $1"; "$SCRIPT_DIR/$1"; fi; }\n'
        'run_optional INSTALL_COMMANDS.sh\n'
        'run_optional restore_node_globals.sh\n'
        'run_optional install_ide_extensions.sh\n'
        'echo "Bootstrap commands completed. Continue with RESTORE_GUIDE.md for manual steps."\n',
        encoding="utf-8",
    )
    script.chmod(0o700)
    return script

def restore(context):
    dest_dir = Path.home() / "Desktop" / "Install_Lists"
    
    # Collect the paths
    brew_dir = context.config_dir / "homebrew"
    app_dir = context.config_dir / "applications"
    disk_dir = context.config_dir / "disk_usage"

    # If nothing is present, skip
    if not brew_dir.exists() and not app_dir.exists() and not disk_dir.exists():
        print('  [SKIP] No system lists found, skipping.')
        return

    if context.dry_run:
        print(f'  [DRY-RUN] Would create folder {dest_dir} containing:')
        print('  [DRY-RUN] - Brewfile, App lists, printer guide/script, download links and disk usage report.')
        return

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        if brew_dir.exists():
            for file in brew_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        if app_dir.exists():
            for file in app_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
            _write_application_install_lists(app_dir, dest_dir)
            _write_application_downloads(app_dir, dest_dir)

        _write_printer_restore_files(context.config_dir.parent, dest_dir)

        if (dest_dir / "Brewfile").exists():
            _write_terminal_install_commands(dest_dir)

        if (dest_dir / "npm-global.json").exists() or (dest_dir / "pnpm-global.json").exists():
            _write_node_global_commands(dest_dir)

        _write_ide_extension_commands(dest_dir)
        _write_bootstrap_commands(dest_dir)
                
        if disk_dir.exists():
            for file in disk_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)

        (dest_dir / "RESTORE_GUIDE.md").write_text(
            "# Mac Restore — quick migration guide\n\n"
            "Run the steps in this order after the clean macOS installation:\n\n"
            "1. `cd ~/Desktop/Install_Lists && ./BOOTSTRAP_MAC.sh` — install Homebrew, Brewfile packages/casks, Node globals and IDE extensions when available.\n"
            "2. Install third-party applications from `applications.txt`, using `APPLICATION_DOWNLOADS.md`.\n"
            "3. Before a live restore of `git_ignored`, install Git and clone or update the tracked project repositories from their remote sources. Mac Restore does not clone repositories or restore tracked source code; if `git_ignored` was already restored, move those files aside before cloning.\n"
            "4. Install printer drivers/software if needed, review `PRINTERS.md`, then optionally run `./restore_printers.sh` and select only the required queues.\n"
            "5. Install MySQL Community Server for Apple Silicon and MySQL Workbench.\n"
            "6. Run `~/Desktop/Database_Restored/restore_mysql.sh` to import the databases.\n"
            "7. Review and manually import keychains from `~/Desktop/MacRestore-Keychains/`.\n"
            "8. Import VPN profiles from `~/Desktop/VPN_Restored/` into Tunnelblick/OpenVPN.\n"
            "9. Open Obsidian and add the vault from `~/Desktop/Obsidian_Vaults_Restored/`.\n"
            "10. Review `Android_Prod_Keys/`, emulator instructions and the generated restore report.\n"
            "11. Reinstall project dependencies and run project-specific generators such as `prisma generate`.\n"
            "12. Test SSH, Git, browsers, printers, MySQL, VPN and development projects.\n\n"
            "## Folder and file map\n\n"
            "- `INSTALL_COMMANDS.sh`: Homebrew installation and `brew bundle`.\n"
            "- `BOOTSTRAP_MAC.sh`: runs the available terminal setup scripts in order.\n"
            "- `services.txt`: Homebrew service state recorded on the source Mac.\n"
            "- `restore_node_globals.sh`: npm/pnpm global package commands.\n"
            "- `install_ide_extensions.sh`: VS Code extension installation commands.\n"
            "- `Brewfile`: formulas and casks recorded on the source Mac.\n"
            "- `applications.txt`: third-party apps to reinstall; macOS apps are excluded.\n"
            "- `applications-full.txt`: complete application inventory for reference.\n"
            "- `APPLICATION_DOWNLOADS.md`: official download pages and MySQL links.\n"
            "- `git_ignored`: restored separately by the `git_ignored` module; contains only ignored local files, not tracked source code.\n"
            "- `PRINTERS.md`: recorded CUPS queues, URIs and driver notes.\n"
            "- `restore_printers.sh`: optional, interactive CUPS queue recreation helper.\n"
            "- `Database_Restored/`: MySQL dumps, guide and import script.\n"
            "- `MacRestore-Keychains/`: keychains for manual import only.\n"
            "- `VPN_Restored/`: VPN profiles for manual import.\n"
            "- `Obsidian_Vaults_Restored/`: restored Obsidian vaults.\n"
            "- `Android_Prod_Keys/`: production mobile keys; handle as secrets.\n"
            "- `VMware_Fusion_Restore.md`: instructions when VMware VMs are inventoried.\n",
            encoding="utf-8",
        )
                
        print(f'  [OK] Installation lists (App/Brew) saved to {dest_dir}')
        print("  [NOTE] Open the terminal, navigate to that folder and run 'brew bundle' to reinstall everything.")
        
    except Exception as e:
        print(f'  [ERROR] Error restoring system_lists: {e}')
