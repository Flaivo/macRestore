import shutil
from pathlib import Path

PLUGIN = {
    "name": "git",
    "description": "Restore global Git configurations (.gitconfig)"
}

def restore(context):
    # During Audit, git is saved in backup_config/git/gitconfig
    source_file = context.config_dir / "git" / "gitconfig"
    dest_file = Path.home() / ".gitconfig"

    if not source_file.exists():
        print('  [SKIP] No .gitconfig found in backup, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        print(f'  [DRY-RUN] Would copy: {source_file}')
        print(f'  [DRY-RUN] To:         {dest_file}')
        if dest_file.exists():
            print('  [DRY-RUN] (The existing .gitconfig would be overwritten)')
        return

    # REAL logic
    try:
        if dest_file.exists():
            backup_esistente = Path.home() / ".gitconfig.pre-restore"
            shutil.copy2(dest_file, backup_esistente)
            print(f'  [NOTE] Backup of existing .gitconfig created at {backup_esistente.name}')

        shutil.copy2(source_file, dest_file)
        print(f'  [OK] .gitconfig successfully restored to {dest_file}')

    except Exception as e:
        print(f'  [ERROR] Error restoring Git: {e}')
