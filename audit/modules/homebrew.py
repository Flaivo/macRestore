from pathlib import Path
import shutil

from shared.inventory import save_inventory
from shared.terminal import run


PLUGIN = {
    "name": "homebrew",
    "description": "Backup Homebrew packages",
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


    data: dict = {
        "installed": False,
        "brew_path": brew_path,
        "services": []
    }


    if not brew_path:

        save_inventory(
            context,
            "homebrew",
            data
        )

        print(
            "Homebrew not found"
        )

        return



    data["installed"] = True


    result = run(
        "brew --version"
    )


    data["version"] = result["stdout"]

    services = run("brew services list")
    if services["success"]:
        services_file = context.config / "homebrew" / "services.txt"
        services_file.parent.mkdir(parents=True, exist_ok=True)
        services_file.write_text(services["output"] + "\n", encoding="utf-8")
        context.register_artifact(services_file)
        data["services"] = services["output"].splitlines()



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

        print("Homebrew backup completed: Brewfile saved.")

        context.register_artifact(brewfile)

    else:

        print(
            "Brewfile error:",
            export["stderr"]
        )
