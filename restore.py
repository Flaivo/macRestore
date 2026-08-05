import sys
import argparse
import subprocess
import getpass
from pathlib import Path

from restore.engine import RestoreEngine
from shared.encryption import decrypted_backup, is_encrypted_backup
from version import __version__
from shared.input import read_number

# Compute the absolute path to the default backups folder
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_BACKUP_DIR = BASE_DIR / "backups"

def get_backup_source():
    """
    Lists backups in the default folder and lets the user select one.
    """
    backups = []
    if DEFAULT_BACKUP_DIR.exists():
        backups = [
            d for d in DEFAULT_BACKUP_DIR.iterdir()
            if (d.is_dir() or is_encrypted_backup(d))
            and not d.name.startswith(".")
        ]
        backups = sorted(backups, key=lambda x: x.name, reverse=True)

    if backups:
        print(f"\nAvailable backups in {DEFAULT_BACKUP_DIR.name}:")
        for index, backup in enumerate(backups, 1):
            marker = " (latest)" if index == 1 else ""
            kind = "encrypted" if is_encrypted_backup(backup) else "directory"
            print(f"{index:2d}. {backup.name}{marker} [{kind}]")
        print(" 0. Browse with Finder")

        selection = read_number(
            "Select the backup to restore (no Enter): ",
            len(backups),
        )
        if selection != "0":
            selected = backups[int(selection) - 1]
            return selected
    else:
        print(f"\nWarning: no backup found in the default folder ({DEFAULT_BACKUP_DIR}).")

    print("Opening Finder...")

    try:
        if DEFAULT_BACKUP_DIR.exists():
            default_location = str(DEFAULT_BACKUP_DIR).replace("\\", "\\\\").replace('"', '\\"')
            apple_script = (
                'tell application "Finder" to activate\n'
                f'POSIX path of (choose folder with prompt "Select the folder containing the backup:" '
                f'default location POSIX file "{default_location}")'
            )
        else:
            apple_script = (
                'tell application "Finder" to activate\n'
                'POSIX path of (choose folder with prompt "Select the folder containing the backup:")'
            )

        risultato = subprocess.run(['osascript', '-e', apple_script], capture_output=True, text=True)
        percorso = risultato.stdout.strip()

        if risultato.returncode != 0:
            error = risultato.stderr.strip()
            if "User canceled" in error or "-128" in error:
                print("No backup selected (cancelled). Exiting.")
            else:
                print(f"Error opening the Finder backup picker: {error or 'unknown AppleScript error'}")
            sys.exit(1)

        if percorso:
            selected = Path(percorso)
            if selected.is_dir() and (selected / "manifest.json").exists():
                return selected

            nested_backups = [
                item for item in selected.iterdir()
                if (item.is_dir() or is_encrypted_backup(item))
                and not item.name.startswith(".")
            ] if selected.is_dir() else []
            nested_backups = sorted(nested_backups, key=lambda item: item.name, reverse=True)

            if nested_backups:
                print(f"\nAvailable backups in {selected.name}:")
                for index, backup in enumerate(nested_backups, 1):
                    marker = " (latest)" if index == 1 else ""
                    kind = "encrypted" if is_encrypted_backup(backup) else "directory"
                    print(f"{index:2d}. {backup.name}{marker} [{kind}]")
                print(" 0. Use the selected folder")
                selection = read_number(
                    "Select the backup to restore (no Enter): ",
                    len(nested_backups),
                )
                if selection != "0":
                    return nested_backups[int(selection) - 1]
            return selected
        else:
            print("No backup selected (cancelled). Exiting.")
            sys.exit(1)
    except Exception as e:
        print(f"Error opening Finder: {e}")
        sys.exit(1)


def select_modules(modules, is_dry_run):
    """Shows an interactive menu to select which modules to restore."""
    print("\n" + "=" * 55)
    print("MAC RESTORE - RESTORE MENU")
    print("=" * 55)
    
    if is_dry_run:
        print("CURRENT MODE: [ DRY-RUN ] (No files will be modified)")
    else:
        print("CURRENT MODE: [ LIVE EXECUTION ] (Files will be overwritten!)")
    print("=" * 55)
    
    print(" 0. Restore ALL modules")
    print("-" * 55)

    for idx, module in enumerate(modules, 1):
        name = module.PLUGIN.get("name", "Unknown")
        desc = module.PLUGIN.get("description", "")
        print(f"{idx:2d}. {name.ljust(15)} : {desc}")

    print("=" * 55)

    scelta = read_number(
        "\nPress 0 for all modules or a module number (no Enter): ",
        len(modules),
    )

    if not scelta or scelta == '0':
        return None

    selezionati_nomi = []
    for item in scelta.split(','):
        item = item.strip()
        if item.isdigit():
            idx = int(item)
            if 1 <= idx <= len(modules):
                nome_modulo = modules[idx - 1].PLUGIN.get("name")
                selezionati_nomi.append(nome_modulo)
            else:
                print(f"Warning: index {idx} out of range, skipped.")
        else:
                print(f"Warning: value '{item}' is not valid, skipped.")

    if not selezionati_nomi:
        print("\nNo valid module selected. Execution cancelled.")
        sys.exit(0)

    return selezionati_nomi


def run_restore(backup_path, dry_run_mode):
    engine = RestoreEngine(backup_path, dry_run=dry_run_mode)
    modules = engine.list_modules()

    if not modules:
        print("Warning: no restore modules found in 'restore/modules/'.")
        return

    selected_names = select_modules(modules, is_dry_run=dry_run_mode)
    engine.run(selected=selected_names)


def main():
    parser = argparse.ArgumentParser(description="Mac Restore - Restore Engine")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Mac Restore {__version__}",
    )
    parser.add_argument("backup_path", nargs="?", help="Path to the backup folder (optional)")
    parser.add_argument("--execute", action="store_true", help="Actually perform the restore (disables dry-run)")
    
    args = parser.parse_args()

    # DRY-RUN logic: without --execute you are safe.
    dry_run_mode = not args.execute

    # Logic to locate the backup
    if args.backup_path:
        backup_path = Path(args.backup_path)
    else:
        backup_path = get_backup_source()

    if not backup_path.exists() or (
        not backup_path.is_dir() and not is_encrypted_backup(backup_path)
    ):
        print(f"Error: the specified backup folder does not exist -> {backup_path}")
        sys.exit(1)

    print(f"\nSelected backup: {backup_path.name}")

    if is_encrypted_backup(backup_path):
        password = getpass.getpass("Backup password: ")
        try:
            with decrypted_backup(backup_path, password) as decrypted_path:
                run_restore(decrypted_path, dry_run_mode)
        except (OSError, ValueError) as error:
            print(f"Cannot open the encrypted backup: {error}")
            sys.exit(1)
    else:
        run_restore(backup_path, dry_run_mode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nRestore operation cancelled by the user.\n")
        sys.exit(0)
