"""Inventory VMware Fusion virtual machines without copying their disks.

VMware virtual machines are bundles (usually ending in ``.vmwarevm``).  They
can be very large, so this module deliberately stores only a small inventory:
the bundle path, its VMX files and basic filesystem metadata.
"""

import os
from datetime import datetime
from pathlib import Path

from shared.inventory import save_inventory


PLUGIN = {
    "name": "vmware",
    "description": "VMware Fusion inventory (virtual disks are not copied)",
    "requires_password": False,
    "has_restore": True,
    "restore_items": ["vmware_virtual_machines"],
}

VMWARE_PATH_ENV = "MAC_RESTORE_VM_PATH"


def _candidate_paths():
    """Return likely VM locations, plus an optional user-supplied path.

    We intentionally do not recursively scan /Volumes: a VM bundle can be
    very large and the scan must remain quick and non-invasive.
    """
    candidates = []
    configured = os.environ.get(VMWARE_PATH_ENV)
    if configured:
        candidates.append(Path(configured).expanduser())

    candidates.extend(
        [
            Path.home() / "Documents" / "Virtual Machines",
            Path.home() / "Documents" / "Virtual Machines.localized",
        ]
    )

    volumes = Path("/Volumes")
    if volumes.exists():
        for volume in volumes.iterdir():
            if volume.is_dir():
                candidates.append(volume)

    # Keep order while removing duplicates.
    return list(dict.fromkeys(candidates))


def _bundles_in(path):
    if path.name.endswith(".vmwarevm") and path.is_dir():
        return [path]
    if not path.is_dir():
        return []
    try:
        return sorted(
            item for item in path.iterdir()
            if item.is_dir() and item.name.endswith(".vmwarevm")
        )
    except OSError:
        return []


def inspect_bundle(bundle):
    """Collect metadata without reading the virtual disk contents."""
    bundle = Path(bundle)
    vmx_files = []
    try:
        vmx_files = sorted(
            str(item.relative_to(bundle))
            for item in bundle.glob("*.vmx")
            if item.is_file()
        )
        stat = bundle.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        readable = os.access(bundle, os.R_OK)
    except OSError:
        modified = None
        readable = False

    return {
        "name": bundle.stem,
        "path": str(bundle),
        "exists": bundle.exists(),
        "readable": readable,
        "vmx_files": vmx_files,
        "modified": modified,
        "disk_contents_backed_up_by_macrestore": False,
    }


def discover_virtual_machines():
    bundles = []
    seen = set()
    for candidate in _candidate_paths():
        for bundle in _bundles_in(candidate):
            resolved = str(bundle.resolve())
            if resolved not in seen:
                seen.add(resolved)
                bundles.append(inspect_bundle(bundle))
    return bundles


def backup(context):
    virtual_machines = discover_virtual_machines()
    result = {
        "virtual_machines": virtual_machines,
        "scan_notes": [
            "Only metadata was saved; .vmwarevm bundles and virtual disks were not copied.",
            f"Set {VMWARE_PATH_ENV} to inventory a custom VM path.",
            "Power off the VM before making an independent copy of its bundle.",
        ],
    }

    inventory_file = save_inventory(context, "vmware", result)
    readable = sum(vm["readable"] for vm in virtual_machines)
    print(
        "VMware inventory completed: "
        f"{len(virtual_machines)} bundles found, {readable} readable, "
        "virtual disks not copied."
    )
    return result
