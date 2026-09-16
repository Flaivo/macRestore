import shutil
from pathlib import Path

PLUGIN = {
    "name": "vpn",
    "description": "Extract VPN profiles (.tblk, .ovpn) to the Desktop for reinstallation"
}

def restore(context):
    source_dir = context.files_dir / "vpn"
    dest_dir = Path.home() / "Desktop" / "VPN_Restored"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print('  [SKIP] No VPN profile found, skipping.')
        return

    # DRY-RUN logic
    if context.dry_run:
        print(f'  [DRY-RUN] Would create folder {dest_dir}')
        profiles = [path for path in source_dir.iterdir() if path.name != '.DS_Store']
        print(f'  [DRY-RUN] Would place {len(profiles)} profiles on the Desktop')
        for file_path in profiles:
            print(f"  [DRY-RUN] Would place profile '{file_path.name}' on the Desktop")
        return

    # REAL logic
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
        (dest_dir / "RESTORE_GUIDE.md").write_text(
            "# VPN restore instructions\n\n"
            "Install the required VPN client first. Review each `.ovpn` and `.tblk` profile, "
            "then import it manually. Treat `.p12` and TLS key files as secrets.\n",
            encoding="utf-8",
        )
        print(f'  [OK] VPN profiles extracted and ready in: {dest_dir}')
        print('  [NOTE] Double-click the .tblk files to re-import them into Tunnelblick.')
    except Exception as e:
        print(f'  [ERROR] Error restoring VPN: {e}')
