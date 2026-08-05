from pathlib import Path
import shutil

from shared.inventory import save_inventory
from shared.filesystem import copy_file, get_file_mode
from shared.exclusions import should_exclude


PLUGIN = {
    "name": "ssh",
    "description": "Backup SSH configuration",
    "requires_password": True,
    "has_restore": True,
    "restore_items": [
        "keys",
        "known_hosts",
        "config"
    ]
}



def backup(context):

    ssh_dir = Path.home() / ".ssh"


    data = {
        "installed": ssh_dir.exists(),
        "files": []
    }


    if not ssh_dir.exists():

        save_inventory(
            context,
            "ssh",
            data
        )

        print(
            "SSH folder not found"
        )

        return


    backup_dir = (
        context.config.parent / "files" /
        "ssh"
    )


    for file in ssh_dir.iterdir():

        if not file.is_file():

            continue


        if should_exclude(file):

            continue


        if file.name.endswith(
            ".sock"
        ):

            continue



        destination = (
            backup_dir /
            file.name
        )


        if copy_file(
            file,
            destination
        ):

            context.register_artifact(
                destination
            )


            data["files"].append(
                {
                    "source": str(
                        file.relative_to(
                            Path.home()
                        )
                    ),
                    "backup": str(
                        destination.relative_to(
                            context.root
                        )
                    ),
                    "restore_to": str(
                        file.relative_to(
                            Path.home()
                        )
                    ),
                    "restore_to": "~/" + str(
                        file.relative_to(
                            Path.home()
                        )
                    ),
                    "mode": get_file_mode(
                        file
                    )
                }
            )



    save_inventory(
        context,
        "ssh",
        data
    )


    print(
        "SSH files:",
        len(
            data["files"]
        )
    )
