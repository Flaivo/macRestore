import shutil
from pathlib import Path

PLUGIN = {
    "name": "mysql",
    "description": "Estrae i dump dei database (.sql.gz) sulla Scrivania"
}

def restore(context):
    source_dir = context.files_dir / "mysql"
    dest_dir = Path.home() / "Desktop" / "Database_Ripristinati"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print("  ⏭️  Nessun dump MySQL trovato, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        print(f"  [DRY-RUN] Creerei la cartella: {dest_dir}")
        for file_path in source_dir.glob("*.sql.gz"):
            print(f"  [DRY-RUN] Estrarrei il dump: {file_path.name}")
        return

    # LOGICA REALE
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.name != ".DS_Store":
                shutil.copy2(file_path, dest_dir / file_path.name)
        print(f"  ✅ Dump dei database estratti con successo in: {dest_dir}")
    except Exception as e:
        print(f"  ❌ Errore nel ripristino di MySQL: {e}")
