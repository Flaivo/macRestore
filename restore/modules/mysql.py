import shutil
import shlex
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
        dump_files = sorted(
            file_path for file_path in source_dir.iterdir()
            if file_path.is_file() and file_path.name.endswith(".sql.gz")
        )
        guide_lines = ["# MySQL restore instructions", "", "Install and start MySQL before importing.", ""]
        script_lines = [
            "#!/bin/sh",
            "set -eu",
            "",
            'SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)',
            'MYSQL_BIN=${MYSQL_BIN:-mysql}',
            'command -v "$MYSQL_BIN" >/dev/null 2>&1 || { echo "mysql command not found. Install and start MySQL first." >&2; exit 1; }',
            "",
            'printf \'MySQL root password (input is hidden): \'',
            'TTY_ECHO_DISABLED=0',
            'if [ -t 0 ]; then stty -echo; TTY_ECHO_DISABLED=1; fi',
            "IFS= read -r MYSQL_ROOT_PASSWORD",
            'if [ "$TTY_ECHO_DISABLED" -eq 1 ]; then stty echo; printf "\\n"; fi',
            'MYSQL_CNF=$(mktemp "${TMPDIR:-/tmp}/macrestore-mysql.XXXXXX")',
            'cleanup() { if [ "$TTY_ECHO_DISABLED" -eq 1 ]; then stty echo 2>/dev/null || true; fi; rm -f -- "$MYSQL_CNF"; unset MYSQL_ROOT_PASSWORD; }',
            "trap cleanup EXIT HUP INT TERM",
            'chmod 600 "$MYSQL_CNF"',
            "printf '[client]\\nuser=root\\npassword=%s\\n' \"$MYSQL_ROOT_PASSWORD\" > \"$MYSQL_CNF\"",
            'unset MYSQL_ROOT_PASSWORD',
            "",
            'echo "Importing MySQL databases..."',
        ]
        for file_path in source_dir.iterdir():
            if file_path.is_file() and file_path.name != ".DS_Store":
                shutil.copy2(file_path, dest_dir / file_path.name)
        for file_path in dump_files:
            database = file_path.name[:-7]
            quoted_dump = '"$SCRIPT_DIR"/' + shlex.quote(file_path.name)
            quoted_database = shlex.quote(database)
            guide_lines.append(
                f"- `{file_path.name}`: `gunzip -c '{file_path.name}' | mysql -u root -p {database}`"
            )
            script_lines.extend([
                f'echo "Preparing database: {database}"',
                f'"$MYSQL_BIN" --defaults-extra-file="$MYSQL_CNF" -e "CREATE DATABASE IF NOT EXISTS {quoted_database};"',
                f"gunzip -c {quoted_dump} | \"$MYSQL_BIN\" --defaults-extra-file=\"$MYSQL_CNF\" {quoted_database}",
                "",
            ])
        script_lines.append('echo "MySQL restore completed."')
        (dest_dir / "RESTORE_GUIDE.md").write_text("\n".join(guide_lines) + "\n", encoding="utf-8")
        script = dest_dir / "restore_mysql.sh"
        script.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
        script.chmod(0o700)
        print(f'  [OK] Database dumps successfully extracted to: {dest_dir}')
        print(f'  [OK] MySQL restore script created: {script}')
    except Exception as e:
        print(f'  [ERROR] Error restoring MySQL: {e}')
