from pathlib import Path
import shutil

from shared.inventory import save_inventory
from shared.filesystem import copy_file


PLUGIN = {
    "name": "git",
    "description": "Backup configurazione Git",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "gitconfig"
    ]
}



def backup(context):

    home = Path.home()

    git_dir = (
        context.config /
        "git"
    )


    files = {
        ".gitconfig": {
            "source": home / ".gitconfig",
            "destination": git_dir / "gitconfig",
            "restore_to": "~/.gitconfig"
        },

        ".gitignore_global": {
            "source": home / ".gitignore_global",
            "destination": git_dir / "gitignore_global",
            "restore_to": "~/.gitignore_global"
        }
    }


    copied = []


    for name, file in files.items():

        if copy_file(
            file["source"],
            file["destination"]
        ):

            context.register_artifact(
                file["destination"]
            )


            copied.append(
                {
                    "source": name,
                    "backup": str(
                        file["destination"].relative_to(
                            context.root
                        )
                    ),
                    "restore_to": file["restore_to"]
                }
            )


    data = {

        "installed": shutil.which(
            "git"
        ) is not None,

        "files": copied
    }


    save_inventory(
        context,
        "git",
        data
    )


    print(
        "Git configurazioni:",
        [
            item["source"]
            for item in copied
        ]
    )