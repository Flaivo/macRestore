from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from shared.plugin_loader import PluginLoader
from shared.progress import Spinner
from shared.report import create_restore_report
from shared.verify import verify_backup
from shared.restore_policy import backup_existing
from shared.processes import running_applications

class RestoreContext:
    def __init__(self, backup_dir, dry_run=True):
        self.backup_dir = Path(backup_dir)
        self.dry_run = dry_run
        
        # Mappiamo le cartelle del backup per comodità nei moduli
        self.inventory_dir = self.backup_dir / "inventory"
        self.config_dir = self.backup_dir / "backup_config"
        self.files_dir = self.backup_dir / "files"
        self._protected_destinations = set()

    def protect_destination(self, destination, label):
        """Create one pre-restore copy for a destination in live mode."""
        destination = Path(destination)
        key = str(destination)
        if self.dry_run or key in self._protected_destinations:
            return None
        self._protected_destinations.add(key)
        return backup_existing(destination, label)

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

        integrity = verify_backup(self.context.backup_dir)
        if "files" in integrity:
            if integrity.get("valid"):
                print("[OK] Backup integrity verified before restore.")
            else:
                print("[ERROR] Backup integrity verification failed. Restore aborted.")
                if self.report_path:
                    create_restore_report(
                        self.report_path,
                        self.context.backup_dir.name,
                        self.context.dry_run,
                        [{"name": "preflight", "status": "failed", "error": "Backup integrity verification failed"}],
                    )
                return []
        else:
            print("[WARNING] checksums.json not found; legacy backup integrity was not verified.")

        print("\n" + "=" * 60)
        print("\nMAC RESTORE - STARTING RESTORE PROCESS")
        print(f"Source: {self.context.backup_dir.name}")
        print("=" * 60)
        
        if self.context.dry_run:
            print("WARNING: DRY-RUN mode active.")
            print("No files will actually be modified on the system.\n")
        else:
            print("WARNING: LIVE EXECUTION mode active.\n")

        open_apps = running_applications()
        if open_apps:
            print("[WARNING] Applications open during restore: " + ", ".join(open_apps))
            print("[WARNING] Close affected applications before live execution.\n")

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
