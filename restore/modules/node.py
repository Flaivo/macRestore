import shutil
from pathlib import Path

PLUGIN = {
    "name": "node",
    "description": "Ripristina le configurazioni di Node (.yarnrc, liste globali)"
}

def restore(context):
    src_dir = context.config_dir / "node"
    home_dir = Path.home()
    lists_dest = Path.home() / "Desktop" / "Install_Lists"

    if not src_dir.exists():
        print("  ⏭️  Nessuna configurazione Node trovata.")
        return

    if context.dry_run:
        print(f"  [DRY-RUN] Ripristinerei .yarnrc/.npmrc in {home_dir}")
        print(f"  [DRY-RUN] Copierei i json dei pacchetti globali in {lists_dest}")
        return

    try:
        lists_dest.mkdir(parents=True, exist_ok=True)
        for file in src_dir.iterdir():
            if file.name.startswith("."):
                shutil.copy2(file, home_dir / file.name)
                print(f"  ✅ Ripristinato file nascosto: {file.name}")
            else:
                shutil.copy2(file, lists_dest / file.name)
                print(f"  ✅ Lista pacchetti {file.name} copiata sulla Scrivania.")
    except Exception as e:
        print(f"  ❌ Errore Node: {e}")
