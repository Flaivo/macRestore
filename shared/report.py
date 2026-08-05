def print_verification(result):

    if result["valid"]:

        print()
        print("[OK] Backup is valid")

    else:

        print()
        print("[ERROR] Backup is invalid")


    print()


    if result.get("error"):
        print("Error:", result["error"])
        return

    for item in result.get("files", []):

        symbol = "[OK]"

        if item["status"] != "ok":
            symbol = "[ERROR]"


        print(
            symbol,
            item["file"],
            "-",
            item["status"]
        )
