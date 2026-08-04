import sys
import argparse
import subprocess
import getpass
from pathlib import Path

from restore.engine import RestoreEngine
from shared.encryption import decrypted_backup, is_encrypted_backup
from version import __version__

# Calcoliamo il percorso assoluto infallibile per la cartella backups di default
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_BACKUP_DIR = BASE_DIR / "backups"

def get_backup_source():
    """
    Trova l'ultimo backup e chiede all'utente se vuole usare quello o aprire il Finder.
    """
    latest_backup = None
    
    # Cerca l'ultimo backup nella cartella di default
    if DEFAULT_BACKUP_DIR.exists():
        backups = [
            d for d in DEFAULT_BACKUP_DIR.iterdir()
            if (d.is_dir() or is_encrypted_backup(d))
            and not d.name.startswith(".")
        ]
        if backups:
            latest_backup = sorted(backups, key=lambda x: x.name, reverse=True)[0]

    if latest_backup:
        print(f"\n📁 Trovato backup di default in: {DEFAULT_BACKUP_DIR.name}")
        scelta = input(f"Vuoi ripristinare l'ultimo backup [{latest_backup.name}]? \n(Premi Invio per confermare, 'y' per cercarne un altro dal Finder): ").strip().lower()
        if scelta != 'y':
            return latest_backup
    else:
        print(f"\n⚠️ Nessun backup trovato nella cartella di default ({DEFAULT_BACKUP_DIR}).")
        print("Apertura del Finder in corso...")
        
    try:
        if DEFAULT_BACKUP_DIR.exists():
            apple_script = f'POSIX path of (choose folder with prompt "Seleziona la cartella del backup da ripristinare:" default location POSIX file "{DEFAULT_BACKUP_DIR}")'
        else:
            apple_script = 'POSIX path of (choose folder with prompt "Seleziona la cartella del backup da ripristinare:")'
        
        risultato = subprocess.run(['osascript', '-e', apple_script], capture_output=True, text=True)
        percorso = risultato.stdout.strip()
        
        if percorso:
            print(f"✅ Backup selezionato dal Finder: {percorso}")
            return Path(percorso)
        else:
            print("❌ Nessuna cartella selezionata (Annullato). Uscita in corso.")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Errore nell'apertura del Finder: {e}")
        sys.exit(1)


def select_modules(modules, is_dry_run):
    """Mostra un menu interattivo per selezionare quali moduli ripristinare."""
    print("\n" + "=" * 55)
    print("🛠️  MAC RESTORE - MENU DI RIPRISTINO")
    print("=" * 55)
    
    # AVVISO GIGANTE DRY-RUN
    if is_dry_run:
        print(" 🟢 MODALITÀ ATTUALE: [ DRY-RUN ] (Nessun file verrà modificato)")
    else:
        print(" 🔴 MODALITÀ ATTUALE: [ ESECUZIONE REALE ] (I file verranno sovrascritti!)")
    print("=" * 55)
    
    print(" 0. Ripristina TUTTI i moduli")
    print("-" * 55)

    for idx, module in enumerate(modules, 1):
        name = module.PLUGIN.get("name", "Sconosciuto")
        desc = module.PLUGIN.get("description", "")
        print(f"{idx:2d}. {name.ljust(15)} : {desc}")

    print("=" * 55)

    scelta = input("\nSeleziona i moduli da ripristinare (es. 0 per tutti, oppure 1,3) [0]: ").strip()

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
                print(f"⚠️  Avviso: Indice {idx} non valido, ignorato.")
        else:
            print(f"⚠️  Avviso: Valore '{item}' non valido, ignorato.")

    if not selezionati_nomi:
        print("\n❌ Nessun modulo valido selezionato. Esecuzione annullata.")
        sys.exit(0)

    return selezionati_nomi


def run_restore(backup_path, dry_run_mode):
    engine = RestoreEngine(backup_path, dry_run=dry_run_mode)
    modules = engine.list_modules()

    if not modules:
        print("⚠️  Nessun modulo di ripristino trovato in 'restore/modules/'.")
        return

    selected_names = select_modules(modules, is_dry_run=dry_run_mode)
    engine.run(selected=selected_names)


def main():
    parser = argparse.ArgumentParser(description="Mac Restore - Motore di Ripristino")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Mac Restore {__version__}",
    )
    parser.add_argument("backup_path", nargs="?", help="Il percorso della cartella del backup (opzionale)")
    parser.add_argument("--execute", action="store_true", help="Esegue REALMENTE il ripristino (disabilita il dry-run)")
    
    args = parser.parse_args()

    # Logica DRY-RUN: Se non metti --execute, sei al sicuro.
    dry_run_mode = not args.execute

    # Logica per trovare il backup
    if args.backup_path:
        backup_path = Path(args.backup_path)
    else:
        backup_path = get_backup_source()

    if not backup_path.exists() or (
        not backup_path.is_dir() and not is_encrypted_backup(backup_path)
    ):
        print(f"❌ Errore: La cartella di backup specificata non esiste -> {backup_path}")
        sys.exit(1)

    if is_encrypted_backup(backup_path):
        password = getpass.getpass("Password del backup: ")
        try:
            with decrypted_backup(backup_path, password) as decrypted_path:
                run_restore(decrypted_path, dry_run_mode)
        except (OSError, ValueError) as error:
            print(f"❌ Impossibile aprire il backup cifrato: {error}")
            sys.exit(1)
    else:
        run_restore(backup_path, dry_run_mode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperazione di ripristino annullata dall'utente.\n")
        sys.exit(0)
