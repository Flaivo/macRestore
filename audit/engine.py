import getpass
import os
import shutil
from datetime import datetime
from pathlib import Path

from shared.plugin_loader import PluginLoader
from shared.filesystem import create_temporary_backup_directory
from shared.context import BackupContext
from shared.manifest import (
    create_manifest,
    save_manifest
)
from config import BACKUP_DIR
from shared.checksum import generate_checksums
from shared.encryption import encrypt_backup_directory, validate_backup_password
from shared.progress import Spinner
from shared.report import create_backup_report, create_backup_summary
from shared.restore_policy import restore_mode
from shared.processes import running_applications


class AuditEngine:

    def __init__(self):

        self.loader = PluginLoader(
            "audit.modules"
        )


    def list_modules(self):

        return self.loader.load_modules()


    def run(self, selected: list[str] | None = None) -> Path | None:

        self._active_plaintext_backup = None

        try:
            return self._run(selected)
        except BaseException:
            self._cleanup_plaintext_backup()
            raise


    def _cleanup_plaintext_backup(self):

        backup_path = self._active_plaintext_backup
        if backup_path is None:
            return

        backup_path = backup_path.resolve()
        if not backup_path.is_dir():
            self._active_plaintext_backup = None
            return

        try:
            shutil.rmtree(backup_path)
            print(f"Removed incomplete plaintext backup: {backup_path}")
        except OSError as error:
            print(f"Error removing incomplete plaintext backup {backup_path}: {error}")
        finally:
            self._active_plaintext_backup = None


    def _run(self, selected: list[str] | None = None) -> Path | None:

        executed_modules = {}

        if selected is None:
            selected = [
                module.PLUGIN["name"]
                for module in self.list_modules()
                if module.PLUGIN.get("default_enabled", True)
            ]

        open_apps = running_applications()
        if (
            open_apps
            and not os.environ.get("MAC_RESTORE_ALLOW_OPEN_APPS")
            and any(name in selected for name in ("browsers", "browser", "obsidian", "remote_tools"))
        ):
            print("[ERROR] Applications open during backup: " + ", ".join(open_apps))
            print("[ERROR] Close them before backing up browser or remote-tool data.")
            print("[ERROR] Set MAC_RESTORE_ALLOW_OPEN_APPS=1 only if you explicitly accept inconsistent data.")
            return None

        backup_path = create_temporary_backup_directory()
        self._active_plaintext_backup = backup_path

        context = BackupContext(backup_path)
        context.prepare()


        for module in self.list_modules():

            name = module.PLUGIN["name"]


            if selected and name not in selected:
                continue


            context.set_module(
                name
            )


            if hasattr(module, "backup"):

                spinner = Spinner(f"Running {name} || ")
                use_spinner = not module.PLUGIN.get(
                    "interactive",
                    module.PLUGIN.get("requires_password", False),
                )
                if use_spinner:
                    spinner.start()

                try:

                    module.backup(context)

                    if use_spinner:
                        spinner.stop(success=True)


                    executed_modules[name] = {
                    "status": "success",
                    "has_restore": module.PLUGIN.get(
                        "has_restore",
                        False
                    ),
                        "restore_items": module.PLUGIN.get(
                            "restore_items",
                            []
                        ),
                        "restore_mode": restore_mode(name),
                    "artifacts": context.artifacts.get(
                        name,
                        []
                    )
                }


                except Exception as error:

                    if use_spinner:
                        spinner.stop(success=False)

                    executed_modules[name] = {
                        "status": "failed",
                        "error": str(error),
                        "has_restore": module.PLUGIN.get(
                            "has_restore",
                            False
                        ),
                        "restore_items": module.PLUGIN.get(
                            "restore_items",
                            []
                        ),
                        "restore_mode": restore_mode(name),
                    }


        manifest = create_manifest(
            executed_modules
        )


        save_manifest(
            backup_path / "manifest.json",
            manifest
        )

        report_file = create_backup_report(backup_path, manifest)

        checksum_spinner = Spinner("Creating checksums")
        checksum_spinner.start()
        checksum_file = generate_checksums(backup_path)
        checksum_spinner.stop(success=True)

        while True:
            password = getpass.getpass(
                "Backup password (at least 8 chars, uppercase, lowercase, digit and special symbol): "
            )
            confirmation = getpass.getpass(
                "Repeat password: "
            )

            if password != confirmation:
                print("Error: passwords do not match. Please try again.")
                continue

            try:
                validate_backup_password(password)
            except ValueError as error:
                print(f"Error: {error}. Please try again.")
                continue

            break

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        backup_name = f"{timestamp}.backup"
        encrypted_path = BACKUP_DIR / backup_name
        duplicate = 1
        while encrypted_path.exists():
            encrypted_path = BACKUP_DIR / f"{timestamp}-{duplicate}.backup"
            duplicate += 1
        encryption_spinner = Spinner("Encrypting backup")
        encryption_spinner.start()
        encrypt_backup_directory(backup_path, encrypted_path, password)
        encryption_spinner.stop(success=True)
        external_report = encrypted_path.with_suffix(".txt")
        create_backup_summary(
            backup_path,
            manifest,
            encrypted_path.name,
            external_report,
        )
        shutil.rmtree(backup_path)
        self._active_plaintext_backup = None

        print()

        print(
            "Backup created:",
            encrypted_path
        )
        print("Backup report:", external_report)


        return encrypted_path
