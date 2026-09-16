from pathlib import Path
import shutil
import subprocess
import getpass

from shared.inventory import save_inventory


PLUGIN = {
    "name": "vpn",
    "description": "macOS VPN configurations",
    "requires_password": True,
    "has_restore": True,
    "restore_items": [
        "tunnelblick_profiles",
        "openvpn_profiles"
    ]
}


HOME = Path.home()


def command_exists(command):
    return shutil.which(command) is not None


def excluded(path):
    blacklist = [
        "node_modules",
        ".git",
        ".Trash"
    ]

    value = str(path)

    return any(
        item in value
        for item in blacklist
    )


def find_tunnelblick_profiles():

    profiles = []

    paths = [
        HOME / "Library/Application Support/Tunnelblick/Configurations",
        HOME / "Library/Application Support/Tunnelblick/Shared",
        Path("/Library/Application Support/Tunnelblick/Shared")
    ]

    for base in paths:

        if not base.exists():
            continue

        for file in base.glob("*.tblk"):

            profiles.append({
                "client": "tunnelblick",
                "active": True,
                "path": str(file)
            })

    return profiles


def find_openvpn_profiles():

    profiles = []

    search_paths = [
        HOME / "Desktop",
        HOME / "Documents",
        HOME / "Downloads",
        HOME / "Chiavi SSL"
    ]

    for base in search_paths:

        if not base.exists():
            continue

        for file in base.rglob("*.ovpn"):

            if excluded(file):
                continue

            profiles.append({
                "client": "openvpn",
                "active": False,
                "path": str(file)
            })

    return profiles


def copy_with_sudo(source, destination, password=None):

    print(f"Permissions required for: {source}")

    try:
        if password is None:
            password = getpass.getpass(
                "macOS password to copy the VPN profile (The password is not saved): "
            )
        if not password:
            print("VPN copy cancelled: no password provided")
            return False

        def run_sudo(arguments):
            return subprocess.run(
                ["sudo", "-S", "-p", "", *arguments],
                input=password + "\n",
                text=True,
                capture_output=True,
                check=True,
            )

        run_sudo(["-v"])
        run_sudo(["ditto", str(source), str(destination)])
        run_sudo(["chown", "-R", getpass.getuser(), str(destination)])


        return True


    except (subprocess.CalledProcessError, OSError) as error:

        print(
            f"sudo copy failed: {error}"
        )

        return False



def copy_profile(source, destination, sudo_password=None):

    protected = str(source).startswith(
        "/Library/Application Support/Tunnelblick"
    )


    if protected:

        return copy_with_sudo(
            source,
            destination,
            sudo_password
        )


    try:

        if source.is_dir():

            shutil.copytree(
                source,
                destination,
                dirs_exist_ok=True
            )

        else:

            shutil.copy2(
                source,
                destination
            )


        return True


    except PermissionError:

        return copy_with_sudo(
            source,
            destination,
            sudo_password
        )

def backup(context):

    tunnelblick = find_tunnelblick_profiles()

    openvpn = find_openvpn_profiles()


    clients = {

        "tunnelblick": (
            Path("/Applications/Tunnelblick.app").exists()
            or (
                HOME
                / "Library/Application Support/Tunnelblick"
            ).exists()
        ),

        "openvpn": command_exists(
            "openvpn"
        )

    }


    data = {

        "installed": (
            clients["tunnelblick"]
            or clients["openvpn"]
        ),

        "clients": clients,

        "profiles": [],

        "certificates": []

    }


    destination_dir = (
        context.config.parent
        / "files"
        / "vpn"
    )

    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    copied_profiles = []
    failed_profiles = []

    protected_profiles = [
        Path(item["path"])
        for item in tunnelblick + openvpn
        if str(item["path"]).startswith("/Library/Application Support/Tunnelblick")
    ]
    sudo_password = None
    if protected_profiles:
        sudo_password = getpass.getpass(
            "macOS password to copy VPN profiles (The password is not saved): "
        )


    for item in tunnelblick + openvpn:


        source = Path(
            item["path"]
        )


        destination = destination_dir / source.name
        # Different source folders frequently contain profiles with the same
        # basename (for example server.ovpn). Never overwrite an earlier profile.
        if destination.exists():
            stem = source.stem
            suffix = source.suffix
            counter = 2
            while destination.exists():
                destination = destination_dir / f"{stem}__{counter}{suffix}"
                counter += 1


        success = copy_profile(
            source,
            destination,
            sudo_password
        )


        if not success:
            failed_profiles.append(str(source))
            continue


        context.register_artifact(
            destination
        )


        copied_profiles.append({

            "client": item["client"],

            "active": item["active"],

            "source": str(source),

            "backup": str(
                destination.relative_to(
                    context.root
                )
            )

        })


    data["profiles"] = copied_profiles
    data["failed_profiles"] = failed_profiles


    save_inventory(
        context,
        "vpn",
        data
    )

    print(
        "VPN backup completed: "
        f"{len(copied_profiles)} profiles saved, "
        f"{len(failed_profiles)} failed."
    )
