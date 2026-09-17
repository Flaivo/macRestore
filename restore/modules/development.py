import shutil
from pathlib import Path

PLUGIN = {
    "name": "development",
    "description": "Restore development configurations (ZSH)"
}

def restore(context):
    source_dir = context.config_dir / "development"
    sources = sorted(
        path for path in source_dir.iterdir()
        if path.is_file() and path.name.startswith(".")
    ) if source_dir.exists() else []

    if not sources:
        print('  [SKIP] No shell configuration found in backup, skipping.')
        return

    if context.dry_run:
        for source in sources:
            destination = Path.home() / source.name
            print(f'  [DRY-RUN] Would copy: {source}')
            print(f'  [DRY-RUN] To:         {destination}')
            if destination.exists():
                print('  [DRY-RUN] (The existing file would be overwritten)')
        return

    try:
        restored = 0
        for source in sources:
            destination = Path.home() / source.name
            if destination.exists():
                context.protect_destination(destination, source.name)
            shutil.copy2(source, destination)
            restored += 1
        print(f'  [OK] Shell configuration restored: {restored} files.')

    except Exception as e:
        print(f'  [ERROR] Error restoring shell configuration: {e}')
