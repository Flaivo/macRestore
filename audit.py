import argparse
import os
import subprocess
import sys
import getpass
from version import __version__

def setup_custom_backup_dir():
    """
    Chiede all'utente se vuole usare una cartella custom PRIMA 
    che i moduli vengano importati, settando una variabile d'ambiente.
    """
    # Se stiamo solo verificando un backup esistente (--verify), saltiamo la domanda
    if len(sys.argv) > 2 and sys.argv[1] == "--verify":
        return

    scelta = input("\nVuoi salvare il backup in una cartella diversa da quella di default? (y/N): ").strip().lower()
    
    if scelta == 'y':
        print("Apertura finestra del Finder in corso...")
        try:
            # Comando AppleScript per aprire il selettore cartelle nativo di macOS
            apple_script = 'POSIX path of (choose folder with prompt "Seleziona la cartella base dove creare il backup:")'
            risultato = subprocess.run(['osascript', '-e', apple_script], capture_output=True, text=True)
            
            percorso_custom = risultato.stdout.strip()
            
            if percorso_custom:
                print(f"✅ Destinazione personalizzata impostata: {percorso_custom}")
                # Salviamo il percorso nell'ambiente per farlo leggere a config.py
                os.environ["MAC_RESTORE_CUSTOM_DIR"] = percorso_custom
            else:
                print("⚠️ Nessuna cartella selezionata (Annullato). Uso la destinazione di default.")
        except Exception as e:
            print(f"⚠️ Errore nell'apertura del Finder: {e}. Uso la destinazione di default.")
    else:
        print("📁 Uso la destinazione di default.")

def select_modules(modules):
    """
    Mostra un menu interattivo per selezionare quali moduli eseguire.
    """
    print("\n" + "=" * 55)
    print("🛠️  MAC RESTORE - MENU DI BACKUP")
    print("=" * 55)
    print(" 0. Esegui TUTTI i moduli (Default)")
    print("-" * 55)

    for idx, module in enumerate(modules, 1):
        name = module.PLUGIN.get("name", "Sconosciuto")
        desc = module.PLUGIN.get("description", "")
        print(f"{idx:2d}. {name.ljust(15)} : {desc}")

    print("=" * 55)

    scelta = input("\nSeleziona i moduli (es. 0 per tutti, oppure 1,3) [0]: ").strip()

    if not scelta or scelta == '0':
        print("\n🚀 Esecuzione di TUTTI i moduli in corso...\n")
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

    print(f"\n🚀 Moduli selezionati per l'esecuzione: {', '.join(selezionati_nomi)}\n")
    return selezionati_nomi

def build_parser():
    parser = argparse.ArgumentParser(description="Mac Restore - Motore di backup e verifica")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Mac Restore {__version__}",
    )
    parser.add_argument(
        "--verify",
        metavar="BACKUP_PATH",
        help="verifica l'integrità di un backup senza avviare la procedura interattiva",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    # Gli import avvengono dopo la scelta della directory: config.py deve leggere
    # l'eventuale variabile MAC_RESTORE_CUSTOM_DIR appena impostata.
    from audit.engine import AuditEngine
    from shared.verify import verify_backup
    from shared.report import print_verification

    if args.verify:
        password = None
        if args.verify.endswith(".backup"):
            password = getpass.getpass("Password del backup: ")
        result = verify_backup(args.verify, password=password)
        print_verification(result)
        return 0

    setup_custom_backup_dir()

    engine = AuditEngine()
    modules = engine.list_modules()

    if not modules:
        print("Nessun modulo disponibile.")
        return 0

    selected_names = select_modules(modules)
    engine.run(selected=selected_names)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperazione annullata dall'utente.\n")
        sys.exit(0)
