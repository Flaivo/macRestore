import json
import platform
import socket
import sys
from datetime import datetime


MANIFEST_VERSION = 2



def create_manifest(modules):

    return {
        "version": MANIFEST_VERSION,
        "created": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "modules": modules
    }



def save_manifest(path, manifest):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4
        )



def load_manifest(path):

    with open(
        path,
        encoding="utf-8"
    ) as file:

        return json.load(file)