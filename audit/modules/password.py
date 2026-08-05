from pathlib import Path
import shutil

from shared.inventory import save_inventory

PLUGIN = {
    "name": "passwords",
    "description": "Backup keychains and browser password databases (Chrome/Arc)",
    "requires_password": False,
    "has_restore": False,
    "restore_items": []
}

def backup_browser_passwords(context, browser_name, base_path):
    """
    Scansiona i profili del browser (Chromium based) e fa il backup dei file 'Login Data'.
    Supporta profili multipli in automatico.
    """
    browser_dir = Path(base_path)
    if not browser_dir.exists():
        return []

    backed_up_profiles = []
    backup_dest_base = context.config.parent / "files" / "passwords" / browser_name.lower()

    # Il file "Local State" contiene info globali del browser, utile da avere insieme alle password
    local_state = browser_dir / "Local State"
    if local_state.exists():
        backup_dest_base.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_state, backup_dest_base / "Local State")

    # Cerchiamo tutte le cartelle che contengono un file "Login Data" (di solito 'Default', 'Profile 1', ecc.)
    for profile_dir in browser_dir.iterdir():
        if profile_dir.is_dir():
            login_data_path = profile_dir / "Login Data"
            if login_data_path.exists():
                # Creiamo la cartella per questo profilo specifico nel backup
                dest_profile_dir = backup_dest_base / profile_dir.name
                dest_profile_dir.mkdir(parents=True, exist_ok=True)
                
                # Copiamo il database delle password
                shutil.copy2(login_data_path, dest_profile_dir / "Login Data")
                backed_up_profiles.append(profile_dir.name)
                
    return backed_up_profiles

def backup(context):
    result = {
        "keychains_backed_up": 0,
        "keychain_files": [],
        "browsers": {
            "chrome": [],
            "arc": []
        }
    }

    # ============================================================
    # 1. BACKUP KEYCHAIN MAC
    # ============================================================
    keychain_dir = Path.home() / "Library" / "Keychains"
    backup_keychain_dir = context.config.parent / "files" / "passwords" / "keychains"

    if keychain_dir.exists():
        backup_keychain_dir.mkdir(parents=True, exist_ok=True)
        
        for ext in ["*.keychain-db", "*.keychain"]:
            for item in keychain_dir.glob(ext):
                dest = backup_keychain_dir / item.name
                shutil.copy2(item, dest)
                result["keychain_files"].append(item.name)

        result["keychains_backed_up"] = len(result["keychain_files"])

    # ============================================================
    # 2. BACKUP GOOGLE CHROME
    # ============================================================
    chrome_path = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    chrome_profiles = backup_browser_passwords(context, "Chrome", chrome_path)
    result["browsers"]["chrome"] = chrome_profiles

    # ============================================================
    # 3. BACKUP ARC BROWSER
    # ============================================================
    # Arc solitamente incapsula i dati Chromium in "User Data"
    arc_path = Path.home() / "Library" / "Application Support" / "Arc" / "User Data"
    if not arc_path.exists():
        # Fallback nel caso la struttura sia leggermente diversa
        arc_path = Path.home() / "Library" / "Application Support" / "Arc"
        
    arc_profiles = backup_browser_passwords(context, "Arc", arc_path)
    result["browsers"]["arc"] = arc_profiles

    # ============================================================
    # 4. SALVATAGGIO INVENTARIO E ARTEFATTI
    # ============================================================
    passwords_base_dir = context.config / "passwords"
    if passwords_base_dir.exists() and hasattr(context, 'register_artifact'):
        context.register_artifact(passwords_base_dir)

    inventory_file = save_inventory(context, "passwords", result)
    print(
        f"Password backup completed: {len(result['keychain_files'])} keychains and "
        f"{sum(len(items) for items in result['browsers'].values())} "
        "browser password databases saved."
    )

    return result
