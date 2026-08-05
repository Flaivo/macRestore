import shutil
from pathlib import Path

PLUGIN = {
    "name": "development",
    "description": "Restore development configurations (ZSH)"
}

def restore(context):
    # Locate the backup file
    source_dir = context.config_dir / "development"
    zshrc_source = source_dir / ".zshrc"

    # Actual destination on the system
    zshrc_dest = Path.home() / ".zshrc"

    # 1. Check that the file exists in the backup
    if not zshrc_source.exists():
        print('  [SKIP] No .zshrc found in backup, skipping.')
        return

    # 2. DRY-RUN logic (Simulation)
    if context.dry_run:
        print(f'  [DRY-RUN] Would copy: {zshrc_source}')
        print(f'  [DRY-RUN] To:         {zshrc_dest}')
        if zshrc_dest.exists():
            print('  [DRY-RUN] (The existing file would be overwritten)')
        return

    # 3. REAL logic (Execution)
    try:
        # If a file already exists, create a quick safety backup before overwriting
        if zshrc_dest.exists():
            backup_existing = Path.home() / ".zshrc.pre-restore"
            shutil.copy2(zshrc_dest, backup_existing)
        print(f'  [NOTE] Backup of existing .zshrc created at {backup_existing.name}')

        shutil.copy2(zshrc_source, zshrc_dest)
        print(f'  [OK] .zshrc successfully restored to {zshrc_dest}')

    except Exception as e:
        print(f'  [ERROR] Error restoring .zshrc: {e}')
