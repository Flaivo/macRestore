import shutil
from pathlib import Path

PLUGIN = {
    "name": "mobile_dev",
    "description": "Ripristina Keystore Android e Xcode Provisioning Profiles"
}

def restore(context):
    base_src = context.files_dir / "mobile_dev"
    android_dest = Path.home() / ".android"
    xcode_dest = Path.home() / "Library" / "MobileDevice" / "Provisioning Profiles"
    prod_keys_dest = Path.home() / "Desktop" / "Android_Prod_Keys"

    if not base_src.exists():
        print("  ⏭️  Nessun dato Mobile Dev trovato.")
        return

    if context.dry_run:
        print(f"  [DRY-RUN] Ripristinerei debug.keystore in {android_dest}")
        print(f"  [DRY-RUN] Ripristinerei Provisioning Profiles in {xcode_dest}")
        print(f"  [DRY-RUN] Metterei le chiavi di produzione (.jks) in {prod_keys_dest}")
        return

    try:
        # Debug Keystore
        debug_src = base_src / "android" / "debug.keystore"
        if debug_src.exists():
            android_dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(debug_src, android_dest / "debug.keystore")
            print("  ✅ Android debug.keystore ripristinato.")

        # Provisioning Profiles
        xcode_src = base_src / "xcode" / "Provisioning Profiles"
        if xcode_src.exists():
            xcode_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(xcode_src, xcode_dest, dirs_exist_ok=True)
            print("  ✅ Xcode Provisioning Profiles ripristinati.")

        # Produzione Keystores
        prod_src = base_src / "android_prod_keys"
        if prod_src.exists():
            prod_keys_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(prod_src, prod_keys_dest, dirs_exist_ok=True)
            print(f"  ✅ Chiavi di produzione Android estratte in {prod_keys_dest}")

    except Exception as e:
        print(f"  ❌ Errore Mobile Dev: {e}")
