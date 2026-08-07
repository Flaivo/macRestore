from pathlib import Path
import subprocess
import shutil
import os
import getpass
import gzip

from shared.inventory import save_inventory


PLUGIN = {
    "name": "mysql",
    "description": "Backup local MySQL databases",
    "requires_password": True,
    "has_restore": True,
    "restore_items": [
        "databases",
        "users"
    ]
}


HOME = Path.home()


# ============================================================
# COMMAND
# ============================================================

def run_command(command, env=None) -> dict:

    try:

        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            env=env
        )

        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }


    except Exception as error:

        return {
            "stdout": "",
            "stderr": str(error),
            "returncode": 1
        }



# ============================================================
# FIND MYSQL
# ============================================================

def find_mysql():

    candidates = [

        "/usr/local/mysql/bin/mysql",

        "/opt/homebrew/bin/mysql",

        "/usr/bin/mysql"

    ]


    for item in candidates:

        if Path(item).exists():

            return item


    return shutil.which("mysql")



# ============================================================
# FIND DUMP
# ============================================================

def find_mysqldump(mysql):

    candidates = [

        str(
            Path(mysql).parent /
            "mysqldump"
        ),

        "/usr/local/mysql/bin/mysqldump",

        "/opt/homebrew/bin/mysqldump",

        shutil.which("mysqldump")

    ]


    for item in candidates:

        if item and Path(item).exists():

            return item


    return None



# ============================================================
# SERVICE
# ============================================================

def mysql_service():

    oracle = run_command(
        "launchctl list | grep com.oracle.oss.mysql"
    )

    if oracle["stdout"]:

        return {
            "type": "oracle",
            "name": "com.oracle.oss.mysql"
        }


    homebrew = run_command(
        "launchctl list | grep homebrew.mxcl.mysql"
    )

    if homebrew["stdout"]:

        return {
            "type": "homebrew",
            "name": "homebrew.mxcl.mysql"
        }


    return None



# ============================================================
# PROCESS
# ============================================================

def mysql_process():

    result = run_command(
        "ps aux | grep '[m]ysqld'"
    )

    return result["stdout"]



# ============================================================
# AUTH
# ============================================================

def mysql_password():

    print()

    print(
        "Local MySQL connection."
    )

    print(
        "Enter the MySQL root password."
    )

    print(
        "This is not your Mac password."
    )

    print(
        "The password is not saved."
    )

    print()


    return getpass.getpass(
        "MySQL root password: "
    )



def mysql_env(password):

    env = os.environ.copy()

    env["MYSQL_PWD"] = password

    return env



# ============================================================
# DATABASE
# ============================================================

def get_databases(mysql, password):
    command = [mysql, "-u", "root", "-N", "-e", "SHOW DATABASES;"]


    result = run_command(
        command,
        mysql_env(password)
    )


    if result["returncode"]:
        raise RuntimeError(
            f"Unable to list MySQL databases: {result['stderr']}"
        )


    excluded = {

        "mysql",
        "sys",
        "information_schema",
        "performance_schema"

    }


    return [

        db.strip()

        for db in result["stdout"].splitlines()

        if db.strip()
        and db.strip() not in excluded

    ]



# ============================================================
# USERS
# ============================================================

def export_users(mysql,password):
    result = subprocess.run(
        [mysql, "-u", "root", "-e", "SELECT user,host FROM mysql.user;"],
        capture_output=True,
        text=True,
        env=mysql_env(password),
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Unable to export MySQL users: {result.stderr.strip()}"
        )

    return result.stdout.strip()



# ============================================================
# DUMP
# ============================================================

def dump_database(
    mysql,
    password,
    database,
    destination
):

    dump = find_mysqldump(mysql)


    if not dump:

        return None



    output = (
        destination /
        f"{database}.sql.gz"
    )


    command = [
        dump, "-u", "root", "--single-transaction", "--routines",
        "--triggers", "--events", "--no-tablespaces",
        "--default-character-set=utf8mb4", "--add-drop-database",
        "--databases", database,
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=mysql_env(password),
            check=False,
        )
        with gzip.open(output, "wb") as compressed_file:
            compressed_file.write(result.stdout) # type: ignore
    except OSError as error:
        return {"database": database, "error": str(error)}

    if result.returncode == 0 and output.exists():

        return {

            "database": database,

            "file": str(output),

            "size": output.stat().st_size

        }


    return {
        "database": database,
        "error": result.stderr.decode(errors="replace").strip()
    }



# ============================================================
# BACKUP
# ============================================================

def backup(context):


    mysql = find_mysql()


    data: dict = {

        "installed": False,

        "binary": None,

        "service": "",

        "process": "",

        "databases": [],

        "dumps": []

    }



    if not mysql:

        save_inventory(
            context,
            "mysql",
            data
        )

        return



    data["installed"] = True

    data["binary"] = mysql

    data["service"] = mysql_service()

    data["process"] = mysql_process()



    password = mysql_password()


    if not password:

        data["error"] = "Password not provided"

        save_inventory(
            context,
            "mysql",
            data
        )

        return



    databases = get_databases(
        mysql,
        password
    )


    data["databases"] = databases

    mysql_dir = (
        context.config.parent / "files" /
        "mysql"
    )



    mysql_dir.mkdir(
        parents=True,
        exist_ok=True
    )



    users = export_users(
        mysql,
        password
    )


    users_file = (
        mysql_dir /
        "mysql_users.txt"
    )

    data["users_file"] = str(
        users_file.relative_to(context.root)
    )


    users_file.write_text(
        users,
        encoding="utf-8"
    )


    context.register_artifact(
        users_file
    )



    for db in databases:

        result = dump_database(

            mysql,

            password,

            db,

            mysql_dir

        )


        if result:

            data["dumps"].append(
                result
            )


            if "file" in result:

                context.register_artifact(
                    Path(result["file"])
                )



    save_inventory(
        context,
        "mysql",
        data
    )


    print(
        "MySQL backup completed"
    )
