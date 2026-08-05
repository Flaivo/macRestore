import shutil
from pathlib import Path

PLUGIN = {
    "name": "password",
    "description": "Restore macOS Keychains (.keychain-db)"
}

def restore(context):
    source_dir = context.files_dir / "passwords" / "keychains"
    dest_dir = Path.home() / "Library" / "Keychains"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print('  [SKIP] No keychain found in backup, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        for file_path in source_dir.glob("*.keychain-db"):
            print(f'  [DRY-RUN] Would copy: {file_path.name}')
            print(f'  [DRY-RUN] To:         {dest_dir}')
            if (dest_dir / file_path.name).exists():
                print('  [DRY-RUN] WARNING: The system keychain will be overwritten.')
        return

    # REAL logic
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)

        restored = 0
        safety_backups = 0
        for file_path in source_dir.glob("*.keychain-db"):
            dest_file = dest_dir / file_path.name
            
            if dest_file.exists():
                backup_esistente = dest_dir / f"{file_path.name}.pre-restore"
                shutil.copy2(dest_file, backup_esistente)
                safety_backups += 1
            
            shutil.copy2(file_path, dest_file)
            restored += 1
            
        print(
            f'  [OK] Keychain restore completed: {restored} restored, '
            f'{safety_backups} existing keychains backed up first.'
        )
        print('  [NOTE] A Mac restart may be required for restored keychains to load correctly.')

    except Exception as e:
        print(f'  [ERROR] Error restoring keychains: {e}')
