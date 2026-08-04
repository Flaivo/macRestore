import shutil
from pathlib import Path

PLUGIN = {
    "name": "password",
    "description": "Ripristina i portachiavi di macOS (.keychain-db)"
}

def restore(context):
    source_dir = context.files_dir / "passwords" / "keychains"
    dest_dir = Path.home() / "Library" / "Keychains"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print("  ⏭️  Nessun portachiavi trovato nel backup, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        for file_path in source_dir.glob("*.keychain-db"):
            print(f"  [DRY-RUN] Copierei: {file_path.name}")
            print(f"  [DRY-RUN] Verso:    {dest_dir}")
            if (dest_dir / file_path.name).exists():
                print(f"  [DRY-RUN] (⚠️ ATTENZIONE: Il portachiavi di sistema verrà sovrascritto!)")
        return

    # LOGICA REALE
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)

        for file_path in source_dir.glob("*.keychain-db"):
            dest_file = dest_dir / file_path.name
            
            if dest_file.exists():
                backup_esistente = dest_dir / f"{file_path.name}.pre-restore"
                shutil.copy2(dest_file, backup_esistente)
                print(f"  💾 Backup del portachiavi esistente salvato in {backup_esistente.name}")
            
            shutil.copy2(file_path, dest_file)
            print(f"  ✅ Portachiavi ripristinato: {file_path.name}")
            
        print("  💡 NOTA: Potrebbe essere necessario riavviare il Mac per far agganciare correttamente i portachiavi ripristinati.")

    except Exception as e:
        print(f"  ❌ Errore nel ripristino dei portachiavi: {e}")
