import shutil
from pathlib import Path

PLUGIN = {
    "name": "remote_tools",
    "description": "Restore databases and preferences of Termius, AnyDesk, FileZilla and TeamViewer"
}

def restore_tool(context, tool_name, source_path, dest_path, is_file=False):
    if not source_path.exists():
        return False
        
    if context.dry_run:
        print(f"  [DRY-RUN] [{tool_name.upper()}] Would copy: {source_path.name} to {dest_path}")
        return True

    try:
        context.protect_destination(dest_path, f"remote_tools/{tool_name}")
        if is_file:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
        else:
            dest_path.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        print(f'  [OK] [{tool_name.upper()}] Restored successfully.')
        return True
    except Exception as e:
        print(f'  [ERROR] Error restoring {tool_name}: {e}')
        return False

def restore(context):
    base_src = context.files_dir / "remote_tools"
    if not base_src.exists():
        print('  [SKIP] No remote tools found, skipping.')
        return

    has_data = False

    # Termius
    if restore_tool(context, "Termius", base_src / "termius" / "Termius", Path.home() / "Library" / "Application Support" / "Termius"):
        has_data = True

    # FileZilla
    if restore_tool(context, "FileZilla", base_src / "filezilla" / "filezilla", Path.home() / ".config" / "filezilla"):
        has_data = True

    # AnyDesk
    if restore_tool(context, "AnyDesk (Config)", base_src / "anydesk" / ".anydesk", Path.home() / ".anydesk"):
        has_data = True
    if restore_tool(context, "AnyDesk (Plist)", base_src / "anydesk" / "com.philandro.anydesk.plist", Path.home() / "Library" / "Preferences" / "com.philandro.anydesk.plist", is_file=True):
        has_data = True

    # TeamViewer
    if restore_tool(context, "TeamViewer (Config)", base_src / "teamviewer" / "TeamViewer", Path.home() / "Library" / "Application Support" / "TeamViewer"):
        has_data = True
    if restore_tool(context, "TeamViewer (Plist)", base_src / "teamviewer" / "com.teamviewer.TeamViewer.plist", Path.home() / "Library" / "Preferences" / "com.teamviewer.TeamViewer.plist", is_file=True):
        has_data = True

    if not has_data:
        print('  [SKIP] No specific remote tools data found in backup, skipping.')
