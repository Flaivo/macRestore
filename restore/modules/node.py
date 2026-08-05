import shutil
from pathlib import Path

PLUGIN = {
    "name": "node",
    "description": "Restore Node configurations (.yarnrc, global lists)"
}

def restore(context):
    src_dir = context.config_dir / "node"
    home_dir = Path.home()
    lists_dest = Path.home() / "Desktop" / "Install_Lists"

    if not src_dir.exists():
        print('  [SKIP] No Node configuration found.')
        return

    if context.dry_run:
        print(f'  [DRY-RUN] Would restore .yarnrc/.npmrc to {home_dir}')
        print(f'  [DRY-RUN] Would copy global package JSON files to {lists_dest}')
        return

    try:
        lists_dest.mkdir(parents=True, exist_ok=True)
        restored_hidden = 0
        restored_lists = 0
        for file in src_dir.iterdir():
            if file.name.startswith("."):
                shutil.copy2(file, home_dir / file.name)
                restored_hidden += 1
            else:
                shutil.copy2(file, lists_dest / file.name)
                restored_lists += 1
        print(
            f'  [OK] Node restore completed: {restored_hidden} config files and '
            f'{restored_lists} package lists restored.'
        )
    except Exception as e:
        print(f'  [ERROR] Node error: {e}')
