import platform

import shutil

from shared.inventory import save_inventory


PLUGIN = {
    "name": "system",
    "description": "macOS system information",
    "requires_password": False,
    "has_restore": False
}



from shared.terminal import run



def backup(context):

    data = {

        "hostname": platform.node(),

        "system": platform.system(),

        "release": platform.release(),

        "version": platform.version(),

        "machine": platform.machine(),

        "processor": platform.processor(),

        "python": platform.python_version(),

        "disk_usage": shutil.disk_usage("/")._asdict(),

        "homebrew": shutil.which(
            "brew"
        ) is not None,

        "mac_model": run(
            "system_profiler SPHardwareDataType | grep 'Model Name'"
        )["stdout"]

    }


    inventory_file = save_inventory(
        context,
        "system",
        data
    )


    print("System inventory completed.")
