import shutil
from pathlib import Path

PLUGIN = {
    "name": "obsidian",
    "description": "Restore Obsidian configurations and Vaults"
}

def restore(context):
    config_src = context.config_dir / "obsidian" / "app_support"
    vaults_src = context.files_dir / "obsidian" / "vaults"
    
    config_dest = Path.home() / "Library" / "Application Support" / "obsidian"
    vaults_dest = Path.home() / "Desktop" / "Obsidian_Vaults_Restored"

    if not config_src.exists() and not vaults_src.exists():
        print('  [SKIP] No Obsidian data found in backup.')
        return

    # DRY-RUN logic
    if context.dry_run:
        if config_src.exists():
            print(f'  [DRY-RUN] Would restore preferences to {config_dest}')
        if vaults_src.exists():
            print(f'  [DRY-RUN] Would place your Vaults in {vaults_dest}')
        return

    # REAL logic
    try:
        if config_src.exists():
            context.protect_destination(config_dest, "Obsidian/config")
            config_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(config_src, config_dest, dirs_exist_ok=True)
            print('  [OK] Obsidian preferences restored.')
            
        if vaults_src.exists():
            context.protect_destination(vaults_dest, "Obsidian/vaults")
            vaults_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(vaults_src, vaults_dest, dirs_exist_ok=True)
            print(f'  [OK] Obsidian vaults extracted to {vaults_dest}')
    except Exception as e:
        print(f'  [ERROR] Error restoring Obsidian: {e}')
