import shutil
from pathlib import Path

PLUGIN = {
    "name": "antigravity",
    "description": "Ripristina settings.json, keybindings e snippets (VS Code / Trae)"
}

def restore(context):
    src_dir = context.config_dir / "antigravity"
    # Di default puntiamo a VS Code (Code/User)
    dest_dir = Path.home() / "Library" / "Application Support" / "Code" / "User"
    desktop_lists = Path.home() / "Desktop" / "Install_Lists"

    if not src_dir.exists():
        print("  ⏭️  Nessuna configurazione IDE trovata.")
        return

    if context.dry_run:
        print(f"  [DRY-RUN] Ripristinerei settings.json e snippets in {dest_dir}")
        print(f"  [DRY-RUN] Estrarrei extensions.txt in {desktop_lists}")
        return

    try:
        user_src = src_dir / "User"
        if user_src.exists():
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(user_src, dest_dir, dirs_exist_ok=True)
            print("  ✅ Configurazioni IDE (VS Code) ripristinate.")

        ext_file = src_dir / "extensions.txt"
        if ext_file.exists():
            desktop_lists.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ext_file, desktop_lists / "vscode_extensions.txt")
            print("  ✅ Lista estensioni salvata sulla Scrivania.")
    except Exception as e:
        print(f"  ❌ Errore IDE: {e}")
