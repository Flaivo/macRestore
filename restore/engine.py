from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from shared.plugin_loader import PluginLoader
from shared.progress import Spinner
from shared.report import create_restore_report

class RestoreContext:
    def __init__(self, backup_dir, dry_run=True):
        self.backup_dir = Path(backup_dir)
        self.dry_run = dry_run
        
        # Mappiamo le cartelle del backup per comodità nei moduli
        self.inventory_dir = self.backup_dir / "inventory"
        self.config_dir = self.backup_dir / "backup_config"
        self.files_dir = self.backup_dir / "files"

class RestoreEngine:

    def __init__(self, backup_path, dry_run=True, report_path=None):
        self.context = RestoreContext(backup_path, dry_run)
        self.report_path = Path(report_path) if report_path else None
        
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

        module_results = []
        for module in modules:
            name = module.PLUGIN.get("name", "Unknown")
            
            if selected and name not in selected:
                continue

            spinner = Spinner(f"Restoring {name}")
            spinner.start()
            output_buffer = StringIO()
            try:
                # Passiamo il context al modulo!
                with redirect_stdout(output_buffer):
                    module.restore(self.context)
                output = output_buffer.getvalue().strip()
                status = "failed" if "[ERROR]" in output else (
                    "skipped" if "[SKIP]" in output and "[OK]" not in output else "success"
                )
                spinner.stop(success=status != "failed")
                if output:
                    print(output)
                module_results.append({"name": name, "status": status, "output": output})
            except Exception as e:
                spinner.stop(success=False)
                print(f"[ERROR] Error while restoring {name}: {e}")
                module_results.append(
                    {"name": name, "status": "failed", "error": str(e), "output": output_buffer.getvalue()}
                )
                
        print("\nProcess completed.\n")
        if self.report_path:
            self.report_path.parent.mkdir(parents=True, exist_ok=True)
            create_restore_report(
                self.report_path,
                self.context.backup_dir.name,
                self.context.dry_run,
                module_results,
            )
            print(f"Restore report: {self.report_path}")
        return module_results
