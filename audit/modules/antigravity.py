from pathlib import Path
import shutil

from shared.inventory import save_inventory

PLUGIN = {
    "name": "antigravity",
    "description": "Configurazioni ed estensioni Antigravity IDE",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "preferences",
        "snippets",
        "extensions_list"
    ]
}

# ============================================================
# MAIN
# ============================================================

def backup(context):
    result = {
        "preferences_backed_up": False,
        "extensions_count": 0,
        "extensions": []
    }

    # ============================================================
    # PERCORSI ANTIGRAVITY IDE (Fork di VS Code)
    # Proviamo diverse varianti per assicurarci di trovarlo
    # ============================================================
    app_support_base = Path.home() / "Library" / "Application Support"
    possible_support_dirs = ["Antigravity IDE", "Antigravity", "antigravity"]
    
    user_dir = None
    for d in possible_support_dirs:
        p = app_support_base / d / "User"
        if p.exists():
            user_dir = p
            break

    possible_ext_dirs = [
        Path.home() / ".antigravity" / "extensions", 
        Path.home() / ".antigravity-ide" / "extensions"
    ]
    
    ext_dir = None
    for d in possible_ext_dirs:
        if d.exists():
            ext_dir = d
            break

    backup_pref_dir = context.config / "antigravity" / "User"

    # ============================================================
    # 1. BACKUP FILE DI CONFIGURAZIONE
    # ============================================================
    if user_dir:
        backup_pref_dir.mkdir(parents=True, exist_ok=True)
        
        # Salviamo solo i file utili per il restore, ignorando cache/storage
        files_to_save = ["settings.json", "keybindings.json", "tasks.json"]
        
        for f in files_to_save:
            src_file = user_dir / f
            if src_file.exists():
                shutil.copy2(src_file, backup_pref_dir)
                result["preferences_backed_up"] = True
                print(f"Copiato: {f}")
        
        # Salviamo gli snippets personalizzati
        snippets_dir = user_dir / "snippets"
        if snippets_dir.exists():
            dest_snippets = backup_pref_dir / "snippets"
            if dest_snippets.exists():
                shutil.rmtree(dest_snippets)
            shutil.copytree(snippets_dir, dest_snippets)
            result["preferences_backed_up"] = True
            print("Copiata cartella: snippets")

        if hasattr(context, 'register_artifact') and result["preferences_backed_up"]:
            context.register_artifact(backup_pref_dir)

    # ============================================================
    # 2. INVENTARIO ESTENSIONI
    # ============================================================
    if ext_dir:
        extensions = set()
        for ext in ext_dir.iterdir():
            # Evitiamo file nascosti o file di sistema
            if ext.is_dir() and not ext.name.startswith("."):
                # I nomi delle cartelle in VS Code sono "publisher.name-1.2.3"
                # Rimuoviamo la versione per avere l'ID esatto dell'estensione
                name_parts = ext.name.rsplit('-', 1)
                
                # Se la seconda parte è composta solo da numeri/punti, è la versione
                if len(name_parts) == 2 and name_parts[1].replace('.', '').isdigit():
                    clean_name = name_parts[0]
                else:
                    clean_name = ext.name
                    
                extensions.add(clean_name)
        
        result["extensions"] = sorted(list(extensions))
        result["extensions_count"] = len(result["extensions"])
        
        # Salviamo la lista in un txt: sarà facilissimo fare un ciclo "for" durante il restore
        ext_list_path = context.config / "antigravity" / "extensions.txt"
        ext_list_path.parent.mkdir(parents=True, exist_ok=True)
        ext_list_path.write_text("\n".join(result["extensions"]), encoding="utf-8")
        
        if hasattr(context, 'register_artifact'):
            context.register_artifact(ext_list_path)
            
        print(f"Creato: {ext_list_path}")

    # ============================================================
    # 3. SALVATAGGIO INVENTARIO JSON
    # ============================================================
    inventory_file = save_inventory(context, "antigravity", result)
    print(f"Creato: {inventory_file}")

    return result
