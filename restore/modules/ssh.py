import os
import shutil
from pathlib import Path

PLUGIN = {
    "name": "ssh",
    "description": "Restore SSH keys and configurations (with restrictive permissions)"
}

def restore(context):
    source_dir = context.files_dir / "ssh"
    dest_dir = Path.home() / ".ssh"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print('  [SKIP] No SSH files found in backup, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        print(f'  [DRY-RUN] Would create folder: {dest_dir} (permissions 700)')
        file_count = sum(file_path.is_file() for file_path in source_dir.iterdir())
        print(f'  [DRY-RUN] Would restore and secure {file_count} SSH files.')
        return

    # REAL logic
    try:
        # Create the .ssh folder if it doesn't exist, with 700 permissions (rwx------)
        dest_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(dest_dir, 0o700)
        # Copy files and set permissions to 600 (rw-------)
        restored = 0
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                dest_file = dest_dir / file_path.name
                
                # Safety backup if something with the same name already exists
                if dest_file.exists():
                    shutil.copy2(dest_file, dest_dir / f"{file_path.name}.pre-restore")
                
                shutil.copy2(file_path, dest_file)
                os.chmod(dest_file, 0o600)
                restored += 1

        print(f'  [OK] SSH restore completed: {restored} files restored and secured.')

    except Exception as e:
        print(f'  [ERROR] Error restoring SSH: {e}')
