from pathlib import Path
import shutil

from shared.inventory import save_inventory
from shared.terminal import run


PLUGIN = {
    "name": "homebrew",
    "description": "Backup pacchetti Homebrew",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "packages"
    ]
}


def backup(context):

    brew_path = shutil.which(
        "brew"
    )


    data = {
        "installed": False,
        "brew_path": brew_path
    }


    if not brew_path:

        save_inventory(
            context,
            "homebrew",
            data
        )

        print(
            "Homebrew non trovato"
        )

        return



    data["installed"] = True


    result = run(
        "brew --version"
    )


    data["version"] = result["stdout"]



    save_inventory(
        context,
        "homebrew",
        data
    )



    brew_dir = (
        context.config /
        "homebrew"
    )


    brew_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    brewfile = (
        brew_dir /
        "Brewfile"
    )


    export = run(
        f"brew bundle dump --file={brewfile} --force"
    )


    if export["success"]:

        context.register_artifact(
            brewfile
        )

        print(
            "Creato:",
            brewfile
        )

        context.register_artifact(brewfile)

    else:

        print(
            "Errore Brewfile:",
            export["stderr"]
        )