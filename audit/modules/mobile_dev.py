from pathlib import Path
import shutil
from shared.inventory import save_inventory

PLUGIN = {
    "name": "mobile_dev",
    "description": "Backup Keystore Android e Xcode Provisioning Profiles",
    "requires_password": False,
    "has_restore": True,
    "restore_items": ["android_keys", "xcode_profiles"]
}

def backup(context):
    result = {"android_keystores": [], "xcode_profiles": 0}
    files_dest = context.config.parent / "files" / "mobile_dev"
    
    # 1. Android Keystore
    android_dir = Path.home() / ".android"
    if android_dir.exists():
        debug_key = android_dir / "debug.keystore"
        if debug_key.exists():
            dest = files_dest / "android" / "debug.keystore"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(debug_key, dest)
            result["android_keystores"].append("debug.keystore")
            print("Copiato Android debug.keystore")

    # 2. Xcode Provisioning Profiles
    prov_dir = Path.home() / "Library" / "MobileDevice" / "Provisioning Profiles"
    if prov_dir.exists():
        dest_prov = files_dest / "xcode" / "Provisioning Profiles"
        shutil.copytree(prov_dir, dest_prov, dirs_exist_ok=True)
        count = len(list(prov_dir.glob("*.mobileprovision")))
        result["xcode_profiles"] = count
        if count > 0:
            print(f"Copiati {count} Xcode Provisioning Profiles")

    save_inventory(context, "mobile_dev", result)
    return result
