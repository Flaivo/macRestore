import shutil
from pathlib import Path

PLUGIN = {
    "name": "system_lists",
    "description": "Estrae Brewfile, liste App e report disco sulla Scrivania"
}

def restore(context):
    dest_dir = Path.home() / "Desktop" / "Install_Lists"
    
    # Raccogliamo i percorsi
    brew_dir = context.config_dir / "homebrew"
    app_dir = context.config_dir / "applications"
    disk_dir = context.config_dir / "disk_usage"

    # Se non c'è niente, saltiamo
    if not brew_dir.exists() and not app_dir.exists() and not disk_dir.exists():
        print("  ⏭️  Nessuna lista di sistema trovata, salto.")
        return

    if context.dry_run:
        print(f"  [DRY-RUN] Creerei la cartella {dest_dir} per contenere:")
        print("  [DRY-RUN] - Brewfile, liste delle App e report dello spazio disco.")
        return

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        if brew_dir.exists():
            for file in brew_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        if app_dir.exists():
            for file in app_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        if disk_dir.exists():
            for file in disk_dir.iterdir():
                shutil.copy2(file, dest_dir / file.name)
                
        print(f"  ✅ Liste di installazione (App/Brew) salvate in {dest_dir}")
        print("  💡 NOTA: Apri il terminale, vai in quella cartella e lancia 'brew bundle' per reinstallare tutto.")
        
    except Exception as e:
        print(f"  ❌ Errore ripristino system_lists: {e}")
