import shutil
from pathlib import Path

PLUGIN = {
    "name": "git_ignored",
    "description": "Ripristina file ignorati da Git (.env, config) nell'albero dei progetti"
}

def restore(context):
    source_dir = context.files_dir / "git_ignored"
    dest_dir = Path.home()

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print("  ⏭️  Nessun file ignorato da Git trovato nel backup, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        print(f"  [DRY-RUN] Ripristinerei l'albero dei progetti da: {source_dir.name}")
        print(f"  [DRY-RUN] Verso la tua cartella utente: {dest_dir}")
        print(f"  [DRY-RUN] (I file .env e le config torneranno nei rispettivi progetti)")
        return

    # LOGICA REALE
    try:
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
        print(f"  ✅ File segreti e ignorati ripristinati con successo nei progetti!")
    except Exception as e:
        print(f"  ❌ Errore nel ripristino di git_ignored: {e}")
