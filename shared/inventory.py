import json
from datetime import datetime



def save_inventory(
    context,
    module_name,
    data
):

    inventory_file = (
        context.inventory /
        f"{module_name}.json"
    )


    payload = {
        "module": module_name,
        "created": datetime.now().isoformat(),
        "data": data
    }


    with open(
        inventory_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            payload,
            file,
            indent=4
        )


    context.register_artifact(
        inventory_file
    )


    return inventory_file