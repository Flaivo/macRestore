import shutil
from pathlib import Path

PLUGIN = {
    "name": "browser",
    "description": "Restore configurations, profiles and passwords for Arc and Chrome"
}

def restore_browser_data(context, browser_name, app_support_path):
    """Helper function to merge data from files/passwords and files/browsers"""
    
    passwords_source = context.files_dir / "passwords" / browser_name
    browsers_source = context.files_dir / "browsers" / browser_name
    dest_dir = Path.home() / "Library" / "Application Support" / app_support_path

    has_data = False

    # 1. Restore general data (Preferences, Bookmarks, Extensions)
    if browsers_source.exists():
        has_data = True
        if context.dry_run:
            print(f'  [DRY-RUN] [{browser_name.upper()}] Would copy preferences to {dest_dir}')
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(browsers_source, dest_dir, dirs_exist_ok=True)
            print(f'  [OK] [{browser_name.upper()}] Preferences and profiles restored.')

    # 2. Restore sensitive databases (Login Data)
    if passwords_source.exists():
        has_data = True
        if context.dry_run:
            print(f'  [DRY-RUN] [{browser_name.upper()}] Would copy Password databases to {dest_dir}')
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(passwords_source, dest_dir, dirs_exist_ok=True)
            print(f'  [OK] [{browser_name.upper()}] Password databases restored.')

    if not has_data:
        print(f'  [SKIP] No data found for {browser_name.upper()}, skipping.')

def restore(context):
    # Ripristina Google Chrome
    restore_browser_data(context, "chrome", "Google/Chrome")
    
    # Ripristina Arc
    restore_browser_data(context, "arc", "Arc")
