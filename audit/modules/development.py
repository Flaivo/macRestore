from pathlib import Path
import shutil

from shared.inventory import save_inventory
from shared.terminal import run_command
from shared.filesystem import copy_file


PLUGIN = {
    "name": "development",
    "description": "macOS development environment",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "config_files",
        "shell_initialization"
    ]
}



def get_version(command):

    result = run_command(
        command
    )

    if result["success"]:

        return result["output"]

    return None



def command_exists(command):

    return shutil.which(
        command
    ) is not None



def backup(context):

    data: dict = {

        "runtime": {

            "node": get_version(
                "node --version"
            ),

            "npm": get_version(
                "npm --version"
            ),

            "pnpm": get_version(
                "pnpm --version"
            ),

            "python": get_version(
                "python3 --version"
            ),

            "git": get_version(
                "git --version"
            )
        },


        "tools": {

            "expo": command_exists(
                "expo"
            ),

            "eas": command_exists(
                "eas"
            ),

            "code": command_exists(
                "code"
            ),

            "brew": command_exists(
                "brew"
            ),

            "android_sdk": (
                Path.home() /
                "Library/Android/sdk"
            ).exists()

        }

    }


    config_files = {
        name: Path.home() / name
        for name in [
            ".npmrc", ".pnpmrc", ".yarnrc", ".yarnrc.yml", ".nvmrc",
            ".zshrc", ".zprofile", ".zshenv", ".zsh_aliases",
            ".bash_profile", ".bashrc", ".profile",
        ]
    }


    copied = []

    destination_dir = (
        context.config /
        "development"
    )


    for name, source in config_files.items():

        destination = (
            destination_dir /
            name
        )


        if copy_file(
            source,
            destination
        ):

            context.register_artifact(
                destination
            )


            copied.append(
                {
                    "source": name,
                    "backup": str(
                        destination.relative_to(
                            context.root
                        )
                    ),
                    "restore_to": f"~/{name}"
                }
            )


    data["config_files"] = copied


    save_inventory(
        context,
        "development",
        data
    )


    print(
        "Development environment detected"
    )
