from pathlib import Path
import shutil
import stat
import tempfile
from datetime import datetime

def copy_directory(

    source,

    destination

):

    try:

        shutil.copytree(

            source,

            destination,

            dirs_exist_ok=True

        )

        return True

    except Exception:

        return False

def create_backup_directory(base_path):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S"
    )

    backup_path = (
        Path(base_path) /
        timestamp
    )

    backup_path.mkdir(
        parents=True,
        exist_ok=True
    )

    return backup_path


def create_temporary_backup_directory():
    """Create a private plaintext staging directory outside the backup target."""
    backup_path = Path(tempfile.mkdtemp(prefix=".macrestore-"))
    backup_path.chmod(0o700)
    return backup_path



def copy_file(
    source,
    destination
):

    source = Path(source)
    destination = Path(destination)


    if not source.exists():

        return False


    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    shutil.copy2(
        source,
        destination
    )


    return True



def get_file_mode(path):

    path = Path(path)

    if not path.exists():

        return None


    return oct(
        stat.S_IMODE(
            path.stat().st_mode
        )
    )
