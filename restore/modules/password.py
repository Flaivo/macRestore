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
            print(f'  [DRY-RUN] Would extract keychain for MANUAL import: {file_path.name}')
        print('  [NOTE] Keychains are never overwritten automatically.')
        return

    # REAL logic
    try:
        export_dir = Path.home() / "Desktop" / "MacRestore-Keychains"
        export_dir.mkdir(parents=True, exist_ok=True)
        restored = 0
        for file_path in source_dir.glob("*.keychain-db"):
            shutil.copy2(file_path, export_dir / file_path.name)
            restored += 1
        print(
            f'  [OK] {restored} keychains extracted to {export_dir} for manual import.'
        )
        print('  [NOTE] Import them with macOS Keychain Access or the security command after review.')

    except Exception as e:
        print(f'  [ERROR] Error restoring keychains: {e}')
