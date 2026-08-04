import shutil
from pathlib import Path

PLUGIN = {
    "name": "development",
    "description": "Ripristina configurazioni di sviluppo (ZSH)"
}

def restore(context):
    # Capiamo dove si trova il file di backup
    source_dir = context.config_dir / "development"
    zshrc_source = source_dir / ".zshrc"

    # La destinazione reale nel sistema
    zshrc_dest = Path.home() / ".zshrc"

    # 1. Verifica che il file esista nel backup
    if not zshrc_source.exists():
        print("  ⏭️  Nessun file .zshrc trovato nel backup, salto.")
        return

    # 2. LOGICA DRY-RUN (Simulazione)
    if context.dry_run:
        print(f"  [DRY-RUN] Copierei: {zshrc_source}")
        print(f"  [DRY-RUN] Verso:    {zshrc_dest}")
        if zshrc_dest.exists():
            print(f"  [DRY-RUN] (Il file esistente verrebbe sovrascritto)")
        return

    # 3. LOGICA REALE (Esecuzione)
    try:
        # Se esiste già un file, ne facciamo una copia di sicurezza rapida prima di sovrascriverlo
        if zshrc_dest.exists():
            backup_esistente = Path.home() / ".zshrc.pre-restore"
            shutil.copy2(zshrc_dest, backup_esistente)
            print(f"  💾 Backup del .zshrc esistente creato in {backup_esistente.name}")

        shutil.copy2(zshrc_source, zshrc_dest)
        print(f"  ✅ .zshrc ripristinato con successo in {zshrc_dest}")

    except Exception as e:
        print(f"  ❌ Errore nel ripristino di .zshrc: {e}")
