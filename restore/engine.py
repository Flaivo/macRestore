from pathlib import Path
from shared.plugin_loader import PluginLoader
from shared.progress import Spinner

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
        print("\nMAC RESTORE - STARTING RESTORE PROCESS")
        print(f"Source: {self.context.backup_dir.name}")
        print("=" * 60)
        
        if self.context.dry_run:
            print("WARNING: DRY-RUN mode active.")
            print("No files will actually be modified on the system.\n")
        else:
            print("WARNING: LIVE EXECUTION mode active.\n")

        for module in modules:
            name = module.PLUGIN.get("name", "Unknown")
            
            if selected and name not in selected:
                continue

            spinner = Spinner(f"Restoring {name}")
            spinner.start()
            try:
                # Passiamo il context al modulo!
                module.restore(self.context)
                spinner.stop(success=True)
            except Exception as e:
                spinner.stop(success=False)
                print(f"[ERROR] Error while restoring {name}: {e}")
                
        print("\nProcess completed.\n")
