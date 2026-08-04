from pathlib import Path
from shared.plugin_loader import PluginLoader

class RestoreContext:
    def __init__(self, backup_dir, dry_run=True):
        self.backup_dir = Path(backup_dir)
        self.dry_run = dry_run
        
        # Mappiamo le cartelle del backup per comodità nei moduli
        self.inventory_dir = self.backup_dir / "inventory"
        self.config_dir = self.backup_dir / "backup_config"
        self.files_dir = self.backup_dir / "files"

class RestoreEngine:

    def __init__(self, backup_path, dry_run=True):
        self.context = RestoreContext(backup_path, dry_run)
        
        # Usiamo il tuo PluginLoader per mantenere l'architettura condivisa
        self.loader = PluginLoader("restore.modules")

    def list_modules(self):
        return self.loader.load_modules()

    def run(self, selected=None):
        modules = self.list_modules()

        print("\n" + "=" * 60)
        print(f"🔄 MAC RESTORE - INIZIO PROCESSO DI RIPRISTINO")
        print(f"📂 Sorgente: {self.context.backup_dir.name}")
        print("=" * 60)
        
        if self.context.dry_run:
            print("⚠️  ATTENZIONE: Modalità DRY-RUN attiva.")
            print("Nessun file verrà realmente modificato sul sistema.\n")
        else:
            print("🔥 ATTENZIONE: Modalità ESECUZIONE REALE attiva.\n")

        for module in modules:
            name = module.PLUGIN.get("name", "Unknown")
            
            if selected and name not in selected:
                continue

            print(f"\n[{name}] Avvio ripristino...")
            try:
                # Passiamo il context al modulo!
                module.restore(self.context)
            except Exception as e:
                print(f"❌ Errore durante il ripristino di {name}: {e}")
                
        print("\n✅ Processo completato.\n")
