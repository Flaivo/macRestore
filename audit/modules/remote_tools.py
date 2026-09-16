from pathlib import Path
import shutil

from shared.inventory import save_inventory
from shared.filesystem import copy_tree_preserving_metadata

PLUGIN = {
    "name": "remote_tools",
    "description": "Backup remote-tool configurations (FileZilla, Termius, AnyDesk, etc.)",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "filezilla",
        "termius",
        "teamviewer",
        "anydesk"
    ]
}

def backup(context):
    result = {
        "backed_up_tools": []
    }

    backup_base_dir = context.config.parent / "files" / "remote_tools"

    # ============================================================
    # PERCORSI TOOL REMOTI
    # Aggiungi qui eventuali altri tool in futuro
    # ============================================================
    tools_paths = {
        "FileZilla": [
            Path.home() / ".config" / "filezilla"
        ],
        "Termius": [
            Path.home() / "Library" / "Application Support" / "Termius"
        ],
        "TeamViewer": [
            Path.home() / "Library" / "Preferences" / "com.teamviewer.TeamViewer.plist",
            Path.home() / "Library" / "Application Support" / "TeamViewer"
        ],
        "AnyDesk": [
            Path.home() / ".anydesk",
            Path.home() / "Library" / "Preferences" / "com.philandro.anydesk.plist"
        ]
    }

    for tool_name, paths in tools_paths.items():
        tool_backed_up = False
        tool_dest_dir = backup_base_dir / tool_name.lower()

        for p in paths:
            if p.exists():
                tool_dest_dir.mkdir(parents=True, exist_ok=True)
                
                if p.is_dir():
                    # Evitiamo di copiare cartelle di cache o log pesanti
                    def ignore_caches(dir_path, contents):
                        excluded = {
                            "Cache", "Code Cache", "GPUCache", "Crashpad", "Logs",
                            "logs", "cache", "session-logs", "thumbnails", "msg_thumbnails",
                            "incoming", "lockfile", "*.lock", "IndexedDB", "Local Storage",
                            "Session Storage", "sentry", "chat", "Cookies", "Network Persistent State",
                            "TransportSecurity", ".DS_Store", ".updaterId", "window-state.json",
                        }
                        return [c for c in contents if c in excluded or c.endswith((".lock", ".trace", "-journal", "-wal", "-shm"))]
                        
                    dest_path = tool_dest_dir / p.name
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    
                    copy_tree_preserving_metadata(p, dest_path, ignore=ignore_caches)
                    tool_backed_up = True
                else:
                    shutil.copy2(p, tool_dest_dir / p.name)
                    tool_backed_up = True

        if tool_backed_up:
            result["backed_up_tools"].append(tool_name)

    if hasattr(context, 'register_artifact') and result["backed_up_tools"]:
        context.register_artifact(backup_base_dir)

    # ============================================================
    # SALVATAGGIO INVENTARIO JSON
    # ============================================================
    inventory_file = save_inventory(context, "remote_tools", result)
    print(
        f"Remote-tool backup completed: {len(result['backed_up_tools'])} tools saved."
    )

    return result
