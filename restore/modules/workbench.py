import shutil
from pathlib import Path

PLUGIN = {
    "name": "workbench",
    "description": "Ripristina le connessioni salvate di MySQL Workbench"
}

def restore(context):
    source_file = context.config_dir / "workbench" / "connections.xml"
    dest_dir = Path.home() / "Library" / "Application Support" / "MySQL" / "Workbench"
    dest_file = dest_dir / "connections.xml"

    if not source_file.exists():
        print("  ⏭️  File connections.xml di Workbench non trovato, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        print(f"  [DRY-RUN] Copierei: connections.xml")
        print(f"  [DRY-RUN] Verso:    {dest_dir}")
        return

    # LOGICA REALE
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest_file)
        print(f"  ✅ Connessioni di MySQL Workbench ripristinate in {dest_dir}")
    except Exception as e:
        print(f"  ❌ Errore nel ripristino di Workbench: {e}")
