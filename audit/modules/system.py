import platform
import re

import shutil

from shared.inventory import save_inventory


PLUGIN = {
    "name": "system",
    "description": "macOS system information",
    "requires_password": False,
    "has_restore": False
}



from shared.terminal import run


def _printer_inventory():
    """Collect CUPS printer queues without copying system-managed files."""
    devices = run("lpstat -v")
    statuses = run("lpstat -p")
    details = run("lpstat -l -p")
    default = run("lpstat -d")

    device_map = {}
    for line in devices.get("stdout", "").splitlines():
        match = re.match(r"^device for (.+?):\s*(.+)$", line.strip())
        if match:
            device_map[match.group(1)] = match.group(2)

    status_map = {}
    for line in statuses.get("stdout", "").splitlines():
        match = re.match(r"^printer (.+?) is (.+)$", line.strip(), re.IGNORECASE)
        if match:
            status_map[match.group(1)] = match.group(2)

    detail_map = {}
    current_name = None
    for line in details.get("stdout", "").splitlines():
        header = re.match(r"^printer (.+?) is ", line.strip(), re.IGNORECASE)
        if header:
            current_name = header.group(1)
            detail_map.setdefault(current_name, {})
            continue
        if current_name:
            detail = line.strip()
            for label in ("Description:", "Interface:", "Make and Model:"):
                if detail.lower().startswith(label.lower()):
                    detail_map[current_name][label[:-1].lower().replace(" ", "_")] = detail[len(label):].strip()

    default_name = ""
    default_match = re.search(
        r"(?:destination for default is|system default destination:)\s*(.+)$",
        default.get("stdout", ""),
        re.IGNORECASE,
    )
    if default_match:
        default_name = default_match.group(1).strip()

    names = sorted(set(device_map) | set(status_map), key=str.casefold)
    printers = [
        {
            "name": name,
            "device_uri": device_map.get(name, ""),
            "status": status_map.get(name, "unknown"),
            "is_default": name == default_name,
            **detail_map.get(name, {}),
        }
        for name in names
    ]
    return {
        "installed": bool(printers),
        "default_printer": default_name,
        "printers": printers,
        "commands": ["lpstat -v", "lpstat -p", "lpstat -l -p", "lpstat -d"],
    }



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
    data["printers"] = _printer_inventory()


    inventory_file = save_inventory(
        context,
        "system",
        data
    )


    print("System inventory completed.")
