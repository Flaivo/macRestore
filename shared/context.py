from pathlib import Path


class BackupContext:

    def __init__(self, backup_path):

        self.root = Path(backup_path)

        self.inventory = (
            self.root /
            "inventory"
        )

        self.config = (
            self.root /
            "backup_config"
        )

        self.files = (
            self.root /
            "files"
        )

        self.current_module = None

        self.artifacts = {}



    def prepare(self):

        self.inventory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.config.mkdir(
            parents=True,
            exist_ok=True
        )

        self.files.mkdir(
            parents=True,
            exist_ok=True
        )



    def set_module(self, module_name):

        self.current_module = module_name

        if module_name not in self.artifacts:

            self.artifacts[module_name] = []



    def register_artifact(self, path):

        if not self.current_module:
            return


        relative = str(
            Path(path).relative_to(
                self.root
            )
        )


        if relative not in self.artifacts[self.current_module]:

            self.artifacts[self.current_module].append(
                relative
            )