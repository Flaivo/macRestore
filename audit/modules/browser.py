from pathlib import Path
import shutil

from shared.inventory import save_inventory

PLUGIN = {
    "name": "browsers",
    "description": "Backup browser data, bookmarks and preferences (Chrome/Arc)",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "bookmarks",
        "preferences",
        "extensions_list",
        "arc_workspaces"
    ]
}

# ============================================================
# UTILS
# ============================================================

def get_extensions_list(profile_dir):
    """
    Estrae gli ID delle estensioni installate nel profilo.
    Salviamo gli ID in un file di testo per evitare di ingigantire il backup
    con centinaia di megabyte di binari scaricabili in automatico.
    """
    ext_dir = profile_dir / "Extensions"
    extensions = []
    if ext_dir.exists():
        for ext in ext_dir.iterdir():
            if ext.is_dir() and not ext.name.startswith("."):
                extensions.append(ext.name)
    return extensions


def backup_browser_data(context, browser_name, base_path):
    """
    Scansiona i profili e salva Segnalibri, Preferenze ed Estensioni.
    """
    browser_dir = Path(base_path)
    if not browser_dir.exists():
        return []

    backed_up_profiles = []
    backup_dest_base = context.config.parent / "files" / "browsers" / browser_name.lower()

    # Iteriamo sulle cartelle per trovare i profili
    for profile_dir in browser_dir.iterdir():
        if profile_dir.is_dir():
            bookmarks_path = profile_dir / "Bookmarks"
            preferences_path = profile_dir / "Preferences"
            
            # Un profilo valido ha almeno uno di questi due file
            if bookmarks_path.exists() or preferences_path.exists():
                dest_profile_dir = backup_dest_base / profile_dir.name
                dest_profile_dir.mkdir(parents=True, exist_ok=True)
                
                profile_info = {
                    "name": profile_dir.name,
                    "bookmarks": False,
                    "preferences": False,
                    "extensions_count": 0
                }

                # 1. Copia Segnalibri
                if bookmarks_path.exists():
                    shutil.copy2(bookmarks_path, dest_profile_dir / "Bookmarks")
                    profile_info["bookmarks"] = True
                    
                # 2. Copia Preferenze (impostazioni, motori di ricerca, etc.)
                if preferences_path.exists():
                    shutil.copy2(preferences_path, dest_profile_dir / "Preferences")
                    profile_info["preferences"] = True

                # 3. Lista Estensioni
                extensions = get_extensions_list(profile_dir)
                if extensions:
                    profile_info["extensions_count"] = len(extensions)
                    ext_file = dest_profile_dir / "extensions.txt"
                    ext_file.write_text("\n".join(extensions), encoding="utf-8")

                backed_up_profiles.append(profile_info)
                
    return backed_up_profiles

# ============================================================
# MAIN
# ============================================================

def backup(context):
    result = {
        "chrome": [],
        "arc": [],
        "arc_special_files": []
    }

    # ============================================================
    # 1. BACKUP GOOGLE CHROME
    # ============================================================
    chrome_path = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    result["chrome"] = backup_browser_data(context, "Chrome", chrome_path)

    # ============================================================
    # 2. BACKUP ARC BROWSER
    # ============================================================
    arc_base = Path.home() / "Library" / "Application Support" / "Arc"
    arc_user_data = arc_base / "User Data"
    
    if not arc_user_data.exists() and arc_base.exists():
        # A seconda della versione, Arc potrebbe non avere la subfolder "User Data"
        arc_user_data = arc_base
        
    result["arc"] = backup_browser_data(context, "Arc", arc_user_data)

    # ============================================================
    # 3. FILE SPECIFICI DI ARC (Spazi, Sidebar, Finestre)
    # ============================================================
    if arc_base.exists():
        arc_dest_base = context.config.parent / "files" / "browsers" / "arc"
        arc_dest_base.mkdir(parents=True, exist_ok=True)
        
        # Arc usa dei file json nella root per salvare la struttura della sidebar
        for storable in arc_base.glob("Storable*.json"):
            shutil.copy2(storable, arc_dest_base / storable.name)
            result["arc_special_files"].append(storable.name)

    # ============================================================
    # 4. SALVATAGGIO INVENTARIO E ARTEFATTI
    # ============================================================
    browsers_base_dir = context.config / "browsers"
    if browsers_base_dir.exists() and hasattr(context, 'register_artifact'):
        context.register_artifact(browsers_base_dir)

    inventory_file = save_inventory(context, "browsers", result)
    profile_count = len(result["chrome"]) + len(result["arc"])
    print(
        f"Browser backup completed: {profile_count} profiles and "
        f"{len(result['arc_special_files'])} Arc special files saved."
    )

    return result
