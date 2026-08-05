import shutil
from pathlib import Path

PLUGIN = {
    "name": "mobile_dev",
    "description": "Restore Android Keystore and Xcode Provisioning Profiles"
}

def restore(context):
    base_src = context.files_dir / "mobile_dev"
    android_dest = Path.home() / ".android"
    xcode_dest = Path.home() / "Library" / "MobileDevice" / "Provisioning Profiles"
    prod_keys_dest = Path.home() / "Desktop" / "Android_Prod_Keys"

    if not base_src.exists():
        print('  [SKIP] No Mobile Dev data found.')
        return

    if context.dry_run:
        print(f'  [DRY-RUN] Would restore debug.keystore to {android_dest}')
        print(f'  [DRY-RUN] Would restore Provisioning Profiles to {xcode_dest}')
        print(f'  [DRY-RUN] Would place production keys (.jks) in {prod_keys_dest}')
        return

    try:
        # Debug Keystore
        debug_src = base_src / "android" / "debug.keystore"
        if debug_src.exists():
            android_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(debug_src, android_dest / "debug.keystore")
            print('  [OK] Android debug.keystore restored.')

        # Provisioning Profiles
        xcode_src = base_src / "xcode" / "Provisioning Profiles"
        if xcode_src.exists():
            xcode_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(xcode_src, xcode_dest, dirs_exist_ok=True)
            print('  [OK] Xcode Provisioning Profiles restored.')

        # Produzione Keystores
        prod_src = base_src / "android_prod_keys"
        if prod_src.exists():
            prod_keys_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(prod_src, prod_keys_dest, dirs_exist_ok=True)
            print(f'  [OK] Android production keys extracted to {prod_keys_dest}')

    except Exception as e:
        print(f'  [ERROR] Mobile Dev error: {e}')
