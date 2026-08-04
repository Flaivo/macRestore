from pathlib import Path
import shutil
import subprocess
import json

from shared.inventory import save_inventory
from shared.filesystem import copy_file


PLUGIN = {
    "name": "node",
    "description": "Ambiente Node.js e package manager",
    "requires_password": False,
    "has_restore": True,
    "restore_items": [
        "node_versions",
        "npm_config",
        "pnpm_config",
        "global_packages"
    ]
}


HOME = Path.home()


def command_exists(command):
    return shutil.which(command) is not None



def run(command):

    try:

        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=True,
            text=True
        )

        return result.stdout.strip()

    except Exception:

        return ""



def command_path(command):

    return shutil.which(command)



def command_version(command):

    result = run(
        f"{command} --version"
    )

    return result



def find_nvm():

    path = HOME / ".nvm"

    return path if path.exists() else None



def current_node_version():

    result = run(
        "nvm current"
    )

    if result and result != "N/A":

        return result.replace(
            "v",
            "",
            1
        )

    return None



def installed_node_versions(nvm_path):

    versions = []


    if not nvm_path:

        return versions


    directory = (
        nvm_path /
        "versions" /
        "node"
    )


    if not directory.exists():

        return versions


    for item in directory.iterdir():

        if item.is_dir():

            versions.append(
                item.name
            )


    return sorted(
        versions
    )



def package_manager_info():

    managers = {}


    for name in [
        "npm",
        "pnpm",
        "yarn"
    ]:

        binary = command_path(name)


        if binary:

            managers[name] = {

                "binary": binary,

                "version":
                    command_version(name)

            }


    return managers



def save_file(context, source, destination):

    if not source.exists():

        return None


    target = (
        context.config /
        destination
    )


    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    copy_file(
        source,
        target
    )


    context.register_artifact(
        target
    )


    return str(
        target.relative_to(
            context.root
        )
    )



def backup_configs(context):

    files = []


    candidates = [

        ".npmrc",

        ".pnpmrc",

        ".yarnrc",

        ".yarnrc.yml",

        ".nvmrc"

    ]


    for name in candidates:

        source = HOME / name


        result = save_file(
            context,
            source,
            f"node/{name}"
        )


        if result:

            files.append(
                result
            )


    return files



def export_global_packages(context):

    output = {}


    if command_exists("npm"):

        data = run(
            "npm list -g --depth=0 --json"
        )

        try:

            output["npm"] = json.loads(
                data
            )

        except Exception:

            output["npm"] = data


        file = (
            context.config /
            "node/npm-global.json"
        )

        file.write_text(
            json.dumps(
                output["npm"],
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )


        context.register_artifact(
            file
        )



    if command_exists("pnpm"):

        data = run(
            "pnpm list -g --depth=0 --json"
        )

        try:

            output["pnpm"] = json.loads(
                data
            )

        except Exception:

            output["pnpm"] = data


        file = (
            context.config /
            "node/pnpm-global.json"
        )

        file.write_text(
            json.dumps(
                output["pnpm"],
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )


        context.register_artifact(
            file
        )


    return output



def backup(context):

    node_binary = command_path(
        "node"
    )


    installed = node_binary is not None


    data = {

        "installed": installed,

        "node": {},

        "package_managers": {},

        "nvm": {},

        "configs": [],

        "global_packages": {}

    }



    if not installed:

        save_inventory(
            context,
            "node",
            data
        )

        return



    data["node"] = {

        "binary":
            node_binary,

        "version":
            command_version(
                "node"
            )

    }



    nvm = find_nvm()


    data["nvm"] = {

        "installed":
            nvm is not None,

        "path":
            str(nvm)
            if nvm else None,

        "current_version":
            current_node_version(),

        "versions":
            installed_node_versions(
                nvm
            )

    }



    data["package_managers"] = (
        package_manager_info()
    )



    data["configs"] = (
        backup_configs(
            context
        )
    )



    data["global_packages"] = (
        export_global_packages(
            context
        )
    )



    save_inventory(
        context,
        "node",
        data
    )


    print(
        "Ambiente Node.js rilevato"
    )
