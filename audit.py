import argparse
import os
import subprocess
import sys
import getpass
from version import __version__
from shared.input import read_key, read_number

def setup_custom_backup_dir():
    """
    Asks the user whether to use a custom folder BEFORE
    modules are imported, by setting an environment variable.
    """
    # If we are only verifying an existing backup (--verify), skip the question
    if len(sys.argv) > 2 and sys.argv[1] == "--verify":
        return

    scelta = read_key(
        "\nChoose a custom backup destination? Default is ./backups/ (y/n): ",
        valid_keys={"y", "n"},
    )
    
    if scelta == 'y':
        print("Opening Finder window...")
        try:
            # AppleScript command to open the native macOS folder picker
            apple_script = 'POSIX path of (choose folder with prompt "Select the base folder where the backup will be created:")'
            risultato = subprocess.run(['osascript', '-e', apple_script], capture_output=True, text=True)
            
            percorso_custom = risultato.stdout.strip()
            
            if percorso_custom:
                print(f"Custom destination set: {percorso_custom}")
                # Save the path in the environment so config.py can read it
                os.environ["MAC_RESTORE_CUSTOM_DIR"] = percorso_custom
            else:
                print("Warning: no folder selected (cancelled). Using the default destination.")
        except Exception as e:
            print(f"Warning: error opening Finder: {e}. Using the default destination.")
    else:
        print("Using the default destination.")

def select_modules(modules):
    """
    Shows an interactive menu to select which modules to run.
    """
    print("\n" + "=" * 55)
    print("MAC RESTORE - BACKUP MENU")
    print("=" * 55)
    default_modules = [
        module for module in modules
        if module.PLUGIN.get("default_enabled", True)
    ]

    print(" 0. Run all standard modules (Default)")
    print("    (Optional modules are listed below and can be selected individually.)")
    print("-" * 55)

    for idx, module in enumerate(modules, 1):
        name = module.PLUGIN.get("name", "Unknown")
        desc = module.PLUGIN.get("description", "")
        optional = " [Optional]" if not module.PLUGIN.get("default_enabled", True) else ""
        print(f"{idx:2d}. {name.ljust(15)}{optional} : {desc}")

    print("=" * 55)

    scelta = read_number(
        "\nPress 0 for all standard modules or a module number (no Enter): ",
        len(modules),
    )

    if not scelta or scelta == '0':
        print("\nRunning all standard modules...\n")
        return [module.PLUGIN.get("name") for module in default_modules]

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

    print(f"\nModules selected for execution: {', '.join(selezionati_nomi)}\n")
    return selezionati_nomi

def build_parser():
    parser = argparse.ArgumentParser(description="Mac Restore - Backup and verification engine")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Mac Restore {__version__}",
    )
    parser.add_argument(
        "--verify",
        metavar="BACKUP_PATH",
        help="verify the integrity of a backup without starting the interactive procedure",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.verify:
        # Per --verify non serve scegliere la cartella, importiamo subito
        from shared.verify import verify_backup
        from shared.report import print_verification

        password = None
        if args.verify.endswith(".backup"):
            password = getpass.getpass("Backup password: ")
        result = verify_backup(args.verify, password=password)
        print_verification(result)
        return 0

    # La scelta della cartella DEVE avvenire prima degli import:
    # config.py legge MAC_RESTORE_CUSTOM_DIR al momento del caricamento del modulo,
    # quindi deve essere settata prima che qualsiasi import la includa.
    setup_custom_backup_dir()

    from audit.engine import AuditEngine

    engine = AuditEngine()
    modules = engine.list_modules()

    if not modules:
        print("No modules available.")
        return 0

    selected_names = select_modules(modules)
    engine.run(selected=selected_names)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by the user.\n")
        sys.exit(0)
    except RuntimeError as error:
        print(f"\nError: {error}\n")
        sys.exit(1)
