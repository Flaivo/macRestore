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
        files = [path for path in source_dir.rglob("*") if path.is_file()]
        print(f'  [DRY-RUN] Would restore project tree from: {source_dir.name}')
        print(f'  [DRY-RUN] To your home folder: {dest_dir}')
        print(f'  [DRY-RUN] Would restore {len(files)} files individually (no full-home copy).')
        print('  [DRY-RUN] (.env files and configs will be back in their respective projects)')
        return

    # REAL logic
    try:
        restored = 0
        for source_file in source_dir.rglob("*"):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source_dir)
            target = dest_dir / relative
            context.protect_destination(target, f"git_ignored/{relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
            restored += 1
        print(f'  [OK] {restored} Git-ignored files restored individually to their projects.')
    except Exception as e:
        print(f'  [ERROR] Error restoring git_ignored: {e}')
