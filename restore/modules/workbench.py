import shutil
from pathlib import Path

PLUGIN = {
    "name": "workbench",
    "description": "Restore saved connections of MySQL Workbench"
}

def restore(context):
    source_file = context.config_dir / "workbench" / "connections.xml"
    dest_dir = Path.home() / "Library" / "Application Support" / "MySQL" / "Workbench"
    dest_file = dest_dir / "connections.xml"

    if not source_file.exists():
        print('  [SKIP] Workbench connections.xml not found, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        print(f"  [DRY-RUN] Would copy: connections.xml")
        print(f"  [DRY-RUN] To:       {dest_dir}")
        return

    # REAL logic
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        context.protect_destination(dest_file, "MySQL-Workbench/connections.xml")
        shutil.copy2(source_file, dest_file)
        print(f'  [OK] MySQL Workbench connections restored to {dest_dir}')
    except Exception as e:
        print(f'  [ERROR] Error restoring Workbench: {e}')
