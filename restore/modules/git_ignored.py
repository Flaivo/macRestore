import shutil
from pathlib import Path

PLUGIN = {
    "name": "git_ignored",
    "description": "Restore Git-ignored files (.env, config) in the project tree"
}

def restore(context):
    source_dir = context.files_dir / "git_ignored"
    dest_dir = Path.home()

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print('  [SKIP] No Git-ignored files found in backup, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        print(f'  [DRY-RUN] Would restore project tree from: {source_dir.name}')
        print(f'  [DRY-RUN] To your home folder: {dest_dir}')
        print('  [DRY-RUN] (.env files and configs will be back in their respective projects)')
        return

    # REAL logic
    try:
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
        print('  [OK] Secret and ignored files successfully restored to projects.')
    except Exception as e:
        print(f'  [ERROR] Error restoring git_ignored: {e}')
