def print_verification(result):

    if result["valid"]:

        print()
        print("Backup integro ✓")

    else:

        print()
        print("Backup non valido ✗")


    print()


    if result.get("error"):
        print("Errore:", result["error"])
        return

    for item in result.get("files", []):

        symbol = "✓"

        if item["status"] != "ok":
            symbol = "✗"


        print(
            symbol,
            item["file"],
            "-",
            item["status"]
        )
