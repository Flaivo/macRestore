import shutil
from pathlib import Path

PLUGIN = {
    "name": "system_lists",
    "description": "Extract Brewfile, application lists and disk report to the Desktop"
}

def restore(context):
    dest_dir = Path.home() / "Desktop" / "Install_Lists"
    
    # Collect the paths
    brew_dir = context.config_dir / "homebrew"
    app_dir = context.config_dir / "applications"
    disk_dir = context.config_dir / "disk_usage"

    # If nothing is present, skip
    if not brew_dir.exists() and not app_dir.exists() and not disk_dir.exists():
        print('  [SKIP] No system lists found, skipping.')
        return

    if context.dry_run:
        print(f'  [DRY-RUN] Would create folder {dest_dir} containing:')
        print('  [DRY-RUN] - Brewfile, App lists and disk usage report.')
        return

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        if brew_dir.exists():
            for file in brew_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        if app_dir.exists():
            for file in app_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        if disk_dir.exists():
            for file in disk_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        print(f'  [OK] Installation lists (App/Brew) saved to {dest_dir}')
        print("  [NOTE] Open the terminal, navigate to that folder and run 'brew bundle' to reinstall everything.")
        
    except Exception as e:
        print(f'  [ERROR] Error restoring system_lists: {e}')
