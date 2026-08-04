import getpass
import shutil

from shared.plugin_loader import PluginLoader
from shared.filesystem import create_backup_directory
from shared.context import BackupContext
from shared.manifest import (
    create_manifest,
    save_manifest
)
from config import BACKUP_DIR
from shared.checksum import generate_checksums
from shared.encryption import encrypt_backup_directory, validate_backup_password


class AuditEngine:

    def __init__(self):

        self.loader = PluginLoader(
            "audit.modules"
        )


    def list_modules(self):

        return self.loader.load_modules()


    def run(self, selected=None):

        backup_path = create_backup_directory(
            BACKUP_DIR
        )

        context = BackupContext(
            backup_path
        )

        context.prepare()


        executed_modules = {}


        for module in self.list_modules():

            name = module.PLUGIN["name"]


            if selected and name not in selected:
                continue


            print(
                f"Esecuzione modulo: {name}"
            )

            context.set_module(
                name
            )


            if hasattr(module, "backup"):

                try:

                    module.backup(context)


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
                    "artifacts": context.artifacts.get(
                        name,
                        []
                    )
                }


                except Exception as error:

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
                        )
                    }


        manifest = create_manifest(
            executed_modules
        )


        save_manifest(
            backup_path / "manifest.json",
            manifest
        )

        checksum_file = generate_checksums(
            backup_path
        )

        print(
            "Checksum creati:",
            checksum_file
        )

        password = getpass.getpass(
            "Password backup (minimo 8 caratteri, maiuscola, minuscola, numero e simbolo speciale): "
        )
        confirmation = getpass.getpass(
            "Ripeti la password: "
        )
        try:
            validate_backup_password(password)
        except ValueError as error:
            raise RuntimeError(str(error)) from error
        if password != confirmation:
            raise RuntimeError("Le password di cifratura non coincidono")

        encrypted_path = backup_path.with_suffix(".backup")
        encrypt_backup_directory(backup_path, encrypted_path, password)
        shutil.rmtree(backup_path)

        print()

        print(
            "Backup creato:",
            encrypted_path
        )


        return encrypted_path
