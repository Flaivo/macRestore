import json
from pathlib import Path
import shutil
from shared.inventory import save_inventory
from shared.filesystem import copy_tree_preserving_metadata

PLUGIN = {
    "name": "obsidian",
    "description": "Backup Obsidian vaults and configurations (without caches)",
    "requires_password": False,
    "has_restore": True,
    "restore_items": ["obsidian_vaults"]
}

def ignore_bloat(dir, contents):
    """Filtra le cartelle spazzatura di Electron e cache varie."""
    bloat_list = {
        'Cache', 'Code Cache', 'Crashpad', 'GPUCache', 'DawnCache',
        'DawnGraphiteCache', 'DawnWebGPUCache', 'SharedStorage', 'Trust Tokens',
        'logs', 'Updates', 'Service Worker',
        'Partitions', 'blob_storage', 'Session Storage', 'IndexedDB',
        'Local Storage', 'WebStorage', 'VideoDecodeStats', 'shared_proto_db',
        'Shared Dictionary', 'SingletonSocket', 'SingletonCookie',
        'SingletonLock', 'Cookies', 'Cookies-journal', 'Network Persistent State',
        'TransportSecurity', 'obsidian.log', 'obsidian-1.13.7.asar', '.DS_Store',
    }
    # Ritorna l'elenco degli elementi in 'contents' che fanno parte della bloat_list
    return [item for item in contents if item in bloat_list or item.endswith(('-wal', '-shm', '-journal'))]

def backup(context):
    result: dict = {"vaults_backed_up": []}
    
    config_dest = context.config / "obsidian"
    files_dest = context.config.parent / "files" / "obsidian"
    
    app_support = Path.home() / "Library" / "Application Support" / "obsidian"
    
    if app_support.exists():
        # Copia preferenze e plugin escludendo la spazzatura di Electron
        copy_tree_preserving_metadata(
            app_support, 
            config_dest / "app_support", 
            ignore=ignore_bloat, 
        )
        
        # Scova e copia i Vault fisici
        obsidian_json = app_support / "obsidian.json"
        if obsidian_json.exists():
            try:
                with open(obsidian_json, "r") as f:
                    data = json.load(f)
                    for v_id, v_data in data.get("vaults", {}).items():
                        v_path = Path(v_data.get("path", ""))
                        if v_path.exists() and v_path.is_dir():
                            vault_dest = files_dest / "vaults" / v_path.name
                            copy_tree_preserving_metadata(v_path, vault_dest)
                            result["vaults_backed_up"].append(v_path.name)
            except Exception as e:
                result["error"] = str(e)

    save_inventory(context, "obsidian", result)
    print(
        "Obsidian backup completed: "
        f"{len(result['vaults_backed_up'])} vaults saved"
        + (" with errors." if result.get("error") else ".")
    )
    return result
