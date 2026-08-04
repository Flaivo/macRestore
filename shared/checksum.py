import json
from pathlib import Path

from shared.hashing import sha256_file



def generate_checksums(
    backup_path
):

    backup_path = Path(
        backup_path
    )

    checksums = {}


    for file in backup_path.rglob("*"):

        if not file.is_file():
            continue

        if file.name == "checksums.json":
            continue


        relative = str(
            file.relative_to(
                backup_path
            )
        )


        checksums[relative] = sha256_file(
            file
        )


    output = (
        backup_path /
        "checksums.json"
    )


    with open(
        output,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            checksums,
            f,
            indent=4
        )


    return output