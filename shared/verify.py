import json
from pathlib import Path

from shared.hashing import sha256_file
from shared.encryption import decrypted_backup, is_encrypted_backup



def verify_backup(
    backup_path,
    password=None,
):

    backup_path = Path(
        backup_path
    ).expanduser().resolve()

    if is_encrypted_backup(backup_path):
        if password is None:
            return {
                "valid": False,
                    "error": "password required for encrypted backup"
            }
        try:
            with decrypted_backup(backup_path, password) as decrypted_path:
                return verify_backup(decrypted_path)
        except (OSError, ValueError) as error:
            return {
                "valid": False,
                "error": str(error)
            }

    if not backup_path.is_dir():
        return {
            "valid": False,
            "error": "backup directory is missing"
        }


    checksum_file = (
        backup_path /
        "checksums.json"
    )


    if not checksum_file.exists():

        return {
            "valid": False,
            "error": "checksums.json is missing"
        }


    try:
        with open(checksum_file, encoding="utf-8") as f:
            checksums = json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        return {
            "valid": False,
            "error": f"checksums.json is not readable: {error}"
        }



    results = []

    valid = True


    for file, expected_hash in checksums.items():
        if not isinstance(file, str):
            results.append({"file": str(file), "status": "invalid_path"})
            valid = False
            continue

        path = (backup_path / file).resolve()
        try:
            path.relative_to(backup_path)
        except ValueError:
            results.append({"file": file, "status": "invalid_path"})
            valid = False
            continue


        if not path.exists():

            results.append(
                {
                    "file": file,
                    "status": "missing"
                }
            )

            valid = False
            continue

        current_hash = sha256_file(path)

        if current_hash == expected_hash:
            results.append({"file": file, "status": "ok"})
        else:
            results.append({"file": file, "status": "modified"})
            valid = False

    # Un file presente nel backup ma assente dal manifest è una modifica,
    # non un backup integro.
    expected_files = set(checksums)
    actual_files = {
        str(path.relative_to(backup_path))
        for path in backup_path.rglob("*")
        if path.is_file() and path.name != "checksums.json"
    }
    for extra in sorted(actual_files - expected_files):
        results.append({"file": extra, "status": "extra"})
        valid = False



    return {
        "valid": valid,
        "files": results
    }
