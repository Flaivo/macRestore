import subprocess



def run(command):

    try:

        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=True,
            text=True
        )


        return {
            "success": result.returncode == 0,

            "output": result.stdout.strip(),

            "stdout": result.stdout.strip(),

            "error": result.stderr.strip(),

            "stderr": result.stderr.strip(),

            "returncode": result.returncode
        }


    except Exception as e:

        return {
            "success": False,

            "output": "",

            "stdout": "",

            "error": str(e),

            "stderr": str(e),

            "returncode": -1
        }



def run_command(command):

    return run(command)
