"""Shared restore safety policy and destination helpers."""

from datetime import datetime
from pathlib import Path
import shutil


RESTORE_MODES = {
    "antigravity": "automatic", "browser": "risky", "development": "automatic",
    "git": "automatic", "git_ignored": "risky", "mobile_dev": "manual",
    "mysql": "manual", "node": "automatic", "obsidian": "manual",
    "password": "manual", "remote_tools": "risky", "ssh": "automatic",
    "system_lists": "inventory", "vmware": "inventory", "vpn": "manual",
    "workbench": "automatic",
}


def restore_mode(module_name):
    return RESTORE_MODES.get(module_name, "manual")


def backup_existing(destination, label):
    """Copy an existing destination before a live restore operation."""
    destination = Path(destination)
    if not destination.exists():
        return None
    root = Path.home() / "Desktop" / "MacRestore-PreRestore" / datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    target = root / label
    target.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_dir():
        shutil.copytree(destination, target, dirs_exist_ok=True)
    else:
        shutil.copy2(destination, target)
    return target
