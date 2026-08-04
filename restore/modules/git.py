import shutil
from pathlib import Path

PLUGIN = {
    "name": "git",
    "description": "Ripristina le configurazioni globali di Git (.gitconfig)"
}

def restore(context):
    # In fase di Audit, git viene salvato in backup_config/git/gitconfig
    source_file = context.config_dir / "git" / "gitconfig"
    dest_file = Path.home() / ".gitconfig"

    if not source_file.exists():
        print("  ⏭️  Nessun .gitconfig trovato nel backup, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        print(f"  [DRY-RUN] Copierei: {source_file}")
        print(f"  [DRY-RUN] Verso:    {dest_file}")
        if dest_file.exists():
            print(f"  [DRY-RUN] (Il .gitconfig esistente verrebbe sovrascritto)")
        return

    # LOGICA REALE
    try:
        if dest_file.exists():
            backup_esistente = Path.home() / ".gitconfig.pre-restore"
            shutil.copy2(dest_file, backup_esistente)
            print(f"  💾 Backup del .gitconfig esistente creato in {backup_esistente.name}")

        shutil.copy2(source_file, dest_file)
        print(f"  ✅ .gitconfig ripristinato con successo in {dest_file}")

    except Exception as e:
        print(f"  ❌ Errore nel ripristino di Git: {e}")
