import shutil
from pathlib import Path

PLUGIN = {
    "name": "mysql",
    "description": "Extract database dumps (.sql.gz) to the Desktop"
}

def restore(context):
    source_dir = context.files_dir / "mysql"
    dest_dir = Path.home() / "Desktop" / "Database_Restored"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print('  [SKIP] No MySQL dump found, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        print(f'  [DRY-RUN] Would create folder: {dest_dir}')
        for file_path in source_dir.glob('*.sql.gz'):
            print(f'  [DRY-RUN] Would extract dump: {file_path.name}')
        return

    # REAL logic
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        guide_lines = ["# MySQL restore instructions", "", "Install and start MySQL before importing.", ""]
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.name != ".DS_Store":
                shutil.copy2(file_path, dest_dir / file_path.name)
                if file_path.name.endswith(".sql.gz"):
                    database = file_path.name[:-7]
                    guide_lines.append(
                        f"- `{file_path.name}`: `gunzip -c '{file_path.name}' | mysql -u root -p {database}`"
                    )
        (dest_dir / "RESTORE_GUIDE.md").write_text("\n".join(guide_lines) + "\n", encoding="utf-8")
        print(f'  [OK] Database dumps successfully extracted to: {dest_dir}')
    except Exception as e:
        print(f'  [ERROR] Error restoring MySQL: {e}')
