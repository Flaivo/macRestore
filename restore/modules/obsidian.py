import shutil
from pathlib import Path

PLUGIN = {
    "name": "obsidian",
    "description": "Ripristina le configurazioni di Obsidian e i Vault"
}

def restore(context):
    config_src = context.config_dir / "obsidian" / "app_support"
    vaults_src = context.files_dir / "obsidian" / "vaults"
    
    config_dest = Path.home() / "Library" / "Application Support" / "obsidian"
    vaults_dest = Path.home() / "Desktop" / "Obsidian_Vaults_Ripristinati"

    if not config_src.exists() and not vaults_src.exists():
        print("  ⏭️  Nessun dato di Obsidian trovato nel backup.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        if config_src.exists():
            print(f"  [DRY-RUN] Ripristinerei le preferenze in {config_dest}")
        if vaults_src.exists():
            print(f"  [DRY-RUN] Metterei i tuoi Vault in {vaults_dest}")
        return

    # LOGICA REALE
    try:
        if config_src.exists():
            config_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(config_src, config_dest, dirs_exist_ok=True)
            print("  ✅ Preferenze di Obsidian ripristinate.")
            
        if vaults_src.exists():
            vaults_dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(vaults_src, vaults_dest, dirs_exist_ok=True)
            print(f"  ✅ Vaults di Obsidian estratti in {vaults_dest}")
    except Exception as e:
        print(f"  ❌ Errore nel ripristino di Obsidian: {e}")
