import os
import shutil
from pathlib import Path

PLUGIN = {
    "name": "ssh",
    "description": "Ripristina chiavi e configurazioni SSH (con permessi restrittivi)"
}

def restore(context):
    source_dir = context.files_dir / "ssh"
    dest_dir = Path.home() / ".ssh"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print("  ⏭️  Nessun file SSH trovato nel backup, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        print(f"  [DRY-RUN] Creerei la cartella: {dest_dir} (permessi 700)")
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                print(f"  [DRY-RUN] Copierei: {file_path.name} in {dest_dir}")
                print(f"  [DRY-RUN] Imposterei i permessi di {file_path.name} a 600")
        return

    # LOGICA REALE
    try:
        # Crea la cartella .ssh se non esiste, con permessi 700 (rwx------)
        dest_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(dest_dir, 0o700)
        print(f"  ✅ Cartella {dest_dir} pronta e sicura.")

        # Copia i file e sistema i permessi a 600 (rw-------)
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                dest_file = dest_dir / file_path.name
                
                # Backup di sicurezza se esiste già qualcosa con lo stesso nome
                if dest_file.exists():
                    shutil.copy2(dest_file, dest_dir / f"{file_path.name}.pre-restore")
                
                shutil.copy2(file_path, dest_file)
                os.chmod(dest_file, 0o600)
                print(f"  🔑 Ripristinato e blindato: {file_path.name}")

    except Exception as e:
        print(f"  ❌ Errore nel ripristino di SSH: {e}")
