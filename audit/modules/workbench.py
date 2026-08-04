from pathlib import Path
import shutil
from shared.inventory import save_inventory

PLUGIN = {
    "name": "workbench",
    "description": "Backup Connessioni MySQL Workbench",
    "requires_password": False,
    "has_restore": True,
    "restore_items": ["mysql_workbench"]
}

def backup(context):
    result = {"connections_saved": False}
    config_dest = context.config / "workbench"
    
    wb_dir = Path.home() / "Library" / "Application Support" / "MySQL" / "Workbench"
    if wb_dir.exists():
        conn_xml = wb_dir / "connections.xml"
        if conn_xml.exists():
            config_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(conn_xml, config_dest / "connections.xml")
            result["connections_saved"] = True
            print("Salvate connessioni MySQL Workbench")

    save_inventory(context, "workbench", result)
    return result
