import shutil
from pathlib import Path

PLUGIN = {
    "name": "antigravity",
    "description": "Restore settings.json, keybindings and snippets (VS Code / Trae)"
}

def restore(context):
    src_dir = context.config_dir / "antigravity"
    # Di default puntiamo a VS Code (Code/User)
    dest_dir = Path.home() / "Library" / "Application Support" / "Code" / "User"
    desktop_lists = Path.home() / "Desktop" / "Install_Lists"

    if not src_dir.exists():
        print('  [SKIP] No IDE configuration found.')
        return

    if context.dry_run:
        print(f'  [DRY-RUN] Would restore settings.json and snippets to {dest_dir}')
        print(f'  [DRY-RUN] Would extract extensions.txt to {desktop_lists}')
        return

    try:
        user_src = src_dir / "User"
        if user_src.exists():
            context.protect_destination(dest_dir, "VSCode/User")
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(user_src, dest_dir, dirs_exist_ok=True)
            print('  [OK] IDE configurations (VS Code) restored.')

        ext_file = src_dir / "extensions.txt"
        if ext_file.exists():
            desktop_lists.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ext_file, desktop_lists / "vscode_extensions.txt")
            print('  [OK] Extensions list saved to Desktop.')
    except Exception as e:
        print(f'  [ERROR] IDE error: {e}')
