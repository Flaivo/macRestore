import shutil
from pathlib import Path

PLUGIN = {
    "name": "browser",
    "description": "Ripristina configurazioni, profili e password di Arc e Chrome"
}

def restore_browser_data(context, browser_name, app_support_path):
    """Funzione helper per unire i dati da files/passwords e files/browsers"""
    
    passwords_source = context.files_dir / "passwords" / browser_name
    browsers_source = context.files_dir / "browsers" / browser_name
    dest_dir = Path.home() / "Library" / "Application Support" / app_support_path

    has_data = False

    # 1. Ripristino dei dati generali (Preferenze, Segnalibri, Estensioni)
    if browsers_source.exists():
        has_data = True
        if context.dry_run:
            print(f"  [DRY-RUN] [{browser_name.upper()}] Copierei le preferenze verso {dest_dir}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(browsers_source, dest_dir, dirs_exist_ok=True)
            print(f"  ✅ [{browser_name.upper()}] Preferenze e profili ripristinati.")

    # 2. Ripristino dei database sensibili (Login Data)
    if passwords_source.exists():
        has_data = True
        if context.dry_run:
            print(f"  [DRY-RUN] [{browser_name.upper()}] Copierei i database delle Password verso {dest_dir}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(passwords_source, dest_dir, dirs_exist_ok=True)
            print(f"  ✅ [{browser_name.upper()}] Database delle password ripristinati.")

    if not has_data:
        print(f"  ⏭️  Nessun dato per {browser_name.upper()} trovato, salto.")

def restore(context):
    # Ripristina Google Chrome
    restore_browser_data(context, "chrome", "Google/Chrome")
    
    # Ripristina Arc
    restore_browser_data(context, "arc", "Arc")
