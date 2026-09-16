"""Interactive entrypoint for Mac Restore."""

import argparse
import getpass
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from shared.input import read_key, read_number
from shared.encryption import decrypted_backup, is_encrypted_backup
from version import __version__


BASE_DIR = Path(__file__).resolve().parent


def _default_backup_dir():
    custom = os.environ.get("MAC_RESTORE_CUSTOM_DIR")
    return Path(custom).expanduser() if custom else BASE_DIR / "backups"


def _header(title):
    print("\n" + "=" * 60)
    print(f"MAC RESTORE - {title}")
    print("=" * 60)


def _pause():
    input("\nPress Enter to return...")


def _choose_backup_destination():
    choice = read_key(
        "\nUse a custom backup destination? [y]es, [n]o, [b]ack: ",
        valid_keys={"y", "n", "b"},
    )
    if choice == "b":
        return False
    if choice == "n":
        os.environ.pop("MAC_RESTORE_CUSTOM_DIR", None)
        print("Using the default ./backups/ destination.")
        return True

    print("Opening Finder...")
    try:
        script = 'POSIX path of (choose folder with prompt "Select the backup destination:")'
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        selected = result.stdout.strip()
        if result.returncode == 0 and selected:
            os.environ["MAC_RESTORE_CUSTOM_DIR"] = selected
            print(f"Custom destination set to: {selected}")
            return True
        print("No folder selected. Returning to the previous menu.")
        return False
    except OSError as error:
        print(f"Could not open Finder: {error}")
        return False


def _select_backup_modules(modules):
    _header("SELECT BACKUP MODULES")
    standard = [module for module in modules if module.PLUGIN.get("default_enabled", True)]
    print(" 1. Run all standard modules")
    print(" 0. Back")
    print("-" * 60)
    for index, module in enumerate(modules, 2):
        optional = " [optional]" if not module.PLUGIN.get("default_enabled", True) else ""
        print(f"{index:2d}. {module.PLUGIN.get('name', 'Unknown')}{optional}")

    choice = read_number("\nSelect a module or an action: ", len(modules) + 1)
    if choice == "0":
        return None
    if choice == "1":
        return [module.PLUGIN["name"] for module in standard]
    module = modules[int(choice) - 2]
    return [module.PLUGIN["name"]]


def _run_backup():
    _header("BACKUP")
    print(" 1. Run all standard modules")
    print(" 2. Select one module")
    print(" 0. Back")
    choice = read_key("\nChoose an action: ", valid_keys={"1", "2", "0"})
    if choice == "0":
        return
    if not _choose_backup_destination():
        return

    # config.py reads the custom destination at import time.
    from audit.engine import AuditEngine

    engine = AuditEngine()
    modules = engine.list_modules()
    if not modules:
        print("No backup modules are available.")
        return

    selected = (
        [module.PLUGIN["name"] for module in modules if module.PLUGIN.get("default_enabled", True)]
        if choice == "1"
        else _select_backup_modules(modules)
    )
    if selected is None:
        return
    engine.run(selected=selected)
    _pause()


def _finder_backup():
    default_dir = _default_backup_dir()
    try:
        script = (
            'tell application "Finder" to activate\n'
            'POSIX path of (choose folder with prompt "Select the folder containing the backup:")'
        )
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except OSError as error:
        print(f"Could not open Finder: {error}")
    return None


def _backup_candidates(folder):
    if not folder.is_dir():
        return []
    return sorted(
        [
            item
            for item in folder.iterdir()
            if (item.is_dir() or is_encrypted_backup(item))
            and not item.name.startswith(".")
        ],
        key=lambda item: item.name,
        reverse=True,
    )


def _select_backup():
    folder = _default_backup_dir()
    candidates = _backup_candidates(folder)
    if not candidates:
        print(f"No backups found in {folder}.")
    else:
        print(f"\nAvailable backups in {folder}:")
        for index, item in enumerate(candidates, 1):
            latest = " (latest)" if index == 1 else ""
            kind = "encrypted" if is_encrypted_backup(item) else "directory"
            print(f"{index:2d}. {item.name}{latest} [{kind}]")
    browse_index = len(candidates) + 1
    print(f"{browse_index:2d}. Browse with Finder")
    print(" 0. Back")
    choice = read_number("\nSelect a backup: ", browse_index)
    if choice == "0":
        return None
    if int(choice) == browse_index:
        selected = _finder_backup()
        if selected and (
            is_encrypted_backup(selected)
            or (selected.is_dir() and ((selected / "manifest.json").exists() or (selected / "backup_report.md").exists()))
        ):
            return selected
        nested = _backup_candidates(selected) if selected else []
        if not nested:
            print("No backup selected.")
            return None
        candidates = nested
        print(f"\nAvailable backups in {selected}:")
        for index, item in enumerate(candidates, 1):
            print(f"{index:2d}. {item.name}")
        choice = read_number("Select a backup or 0 to go back: ", len(candidates))
        if choice == "0":
            return None
    return candidates[int(choice) - 1]


def _show_backup_details(backup_path):
    if is_encrypted_backup(backup_path):
        password = getpass.getpass("Backup password: ")
        try:
            with decrypted_backup(backup_path, password) as decrypted:
                report = decrypted / "backup_report.md"
                if report.exists():
                    print("\n" + report.read_text(encoding="utf-8"))
                else:
                    print("Detailed report is not available in this backup.")
        except (OSError, ValueError) as error:
            print(f"Cannot open backup details: {error}")
    else:
        report = Path(backup_path) / "backup_report.md"
        if report.exists():
            print("\n" + report.read_text(encoding="utf-8"))
        else:
            print("Detailed report is not available in this backup.")
    _pause()


def _select_restore_modules(modules):
    _header("SELECT RESTORE MODULES")
    print(" 1. Restore all modules")
    print(" 0. Back")
    print("-" * 60)
    for index, module in enumerate(modules, 2):
        print(
            f"{index:2d}. {module.PLUGIN.get('name', 'Unknown')} "
            f"[{module.PLUGIN.get('restore_mode', 'manual')}]"
        )
    choice = read_number("\nSelect a module or an action: ", len(modules) + 1)
    if choice == "0":
        return False
    if choice == "1":
        return None
    return [modules[int(choice) - 2].PLUGIN["name"]]


def _run_restore(backup_path):
    mode = read_key(
        "\nRestore mode: [1] dry-run, [2] live execution, [0] back: ",
        valid_keys={"1", "2", "0"},
    )
    if mode == "0":
        return
    dry_run = mode == "1"
    restore_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    report_path = backup_path.parent / (
        f"{backup_path.stem}_restore_{restore_timestamp}.txt"
    )
    duplicate = 1
    while report_path.exists():
        report_path = backup_path.parent / (
            f"{backup_path.stem}_restore_{restore_timestamp}-{duplicate}.txt"
        )
        duplicate += 1

    def restore_from(path):
        from restore.engine import RestoreEngine

        engine = RestoreEngine(path, dry_run=dry_run, report_path=report_path)
        modules = engine.list_modules()
        selected = _select_restore_modules(modules)
        if selected is False:
            return False
        if not dry_run:
            confirmation = input(
                "LIVE restore will modify existing files. Type RESTORE to continue: "
            )
            if confirmation.strip() != "RESTORE":
                print("Live restore cancelled.")
                return False
        if selected is None:
            engine.run()
        else:
            engine.run(selected=selected)
        return True

    completed = False
    if is_encrypted_backup(backup_path):
        password = getpass.getpass("Backup password: ")
        try:
            with decrypted_backup(backup_path, password) as decrypted:
                completed = restore_from(decrypted)
        except (OSError, ValueError) as error:
            print(f"Cannot open backup: {error}")
    else:
        completed = restore_from(backup_path)
    _pause()
    return completed


def _restore_menu():
    _header("RESTORE")
    backup = _select_backup()
    if backup is None:
        return
    while True:
        _header(f"SELECTED BACKUP: {backup.name}")
        print(" 1. Restore")
        print(" 2. View backup details")
        print(" 0. Back")
        choice = read_key("\nChoose an action: ", valid_keys={"1", "2", "0"})
        if choice == "0":
            return
        if choice == "1":
            if _run_restore(backup):
                print("Restore completed. Exiting Mac Restore.")
                return True
        else:
            _show_backup_details(backup)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mac Restore interactive application")
    parser.add_argument("--version", action="version", version=f"Mac Restore {__version__}")
    parser.parse_args(argv)

    while True:
        _header("MAIN MENU")
        print(" 1. Backup")
        print(" 2. Restore")
        print(" 0. Exit")
        choice = read_key("\nChoose an action: ", valid_keys={"1", "2", "0"})
        if choice == "0":
            print("Goodbye.")
            return 0
        if choice == "1":
            _run_backup()
        else:
            if _restore_menu():
                print("Goodbye.")
                return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
