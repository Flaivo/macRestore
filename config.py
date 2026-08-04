import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Legge la variabile d'ambiente, se è stata impostata dal Finder usa quella, altrimenti il default
custom_backup_dir = os.environ.get("MAC_RESTORE_CUSTOM_DIR")

if custom_backup_dir:
    BACKUP_DIR = Path(custom_backup_dir)
else:
    BACKUP_DIR = BASE_DIR / "backups"

INVENTORY_DIR = "inventory"
BACKUP_CONFIG_DIR = "backup_config"
