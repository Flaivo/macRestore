import importlib
import pkgutil
from shared.restore_policy import restore_mode


class PluginLoader:

    def __init__(self, package):
        self.package = package


    def load_modules(self):
        modules = []

        package = importlib.import_module(self.package)

        for _, name, _ in pkgutil.iter_modules(
            package.__path__
        ):

            if name.startswith("_"):
                continue

            module = importlib.import_module(
                f"{self.package}.{name}"
            )

            if hasattr(module, "PLUGIN"):
                module.PLUGIN.setdefault(
                    "restore_mode", restore_mode(module.PLUGIN.get("name", ""))
                )
                modules.append(module)

        return sorted(
            modules,
            key=lambda x: x.PLUGIN["name"]
        )


    def get_module(self, name):

        modules = self.load_modules()

        for module in modules:
            if module.PLUGIN["name"] == name:
                return module

        return None
