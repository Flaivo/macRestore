"""Small macOS process checks used to keep application data consistent."""

import subprocess


APPLICATIONS = {
    "Google Chrome": "Google Chrome",
    "Arc": "Arc",
    "Obsidian": "Obsidian",
    "MySQL Workbench": "MySQLWorkbench",
    "Termius": "Termius",
    "FileZilla": "filezilla",
    "AnyDesk": "AnyDesk",
    "TeamViewer": "TeamViewer",
}


def running_applications():
    try:
        result = subprocess.run(
            ["ps", "-axo", "comm="], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    processes = {line.strip().rsplit("/", 1)[-1] for line in result.stdout.splitlines()}
    return [name for name, process in APPLICATIONS.items() if process in processes]
