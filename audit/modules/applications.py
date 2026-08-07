from pathlib import Path
import subprocess
import shutil
import plistlib

from shared.inventory import save_inventory

PLUGIN = {
    "name": "applications",
    "description": "Installed macOS applications",
    "requires_password": False,
    "has_restore": False,
    "restore_items": [
        "applications_list"
    ]
}

# ============================================================
# COMMAND
# ============================================================

def run_command(command) -> dict:
    try:
        result = subprocess.run(
            command,
            shell=isinstance(command, str),
            capture_output=True,
            text=True
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": 1
        }

# ============================================================
# APP VERSION
# ============================================================

def get_app_version(app):
    plist = app / "Contents" / "Info.plist"

    if not plist.exists():
        return None

    try:
        # Molto più veloce rispetto a lanciare PlistBuddy tramite subprocess
        with open(plist, 'rb') as f:
            parsed_plist = plistlib.load(f)
            return parsed_plist.get("CFBundleShortVersionString", parsed_plist.get("CFBundleVersion"))
    except Exception:
        return None

# ============================================================
# APPLICATIONS
# ============================================================

def scan_applications():
    locations = [
        Path("/Applications"),
        Path("/System/Applications"), # Aggiunto per catturare anche le app native moderne
        Path.home() / "Applications"
    ]

    applications = []

    for location in locations:
        if not location.exists():
            continue

        for app in location.glob("*.app"):
            applications.append({
                "name": app.stem,
                "path": str(app),
                "version": get_app_version(app)
            })

    return sorted(
        applications,
        key=lambda x: x["name"].lower()
    )

# ============================================================
# HOMEBREW CASK
# ============================================================

def get_brew_casks():
    if not shutil.which("brew"):
        return []

    result = run_command("brew list --cask")

    if result["returncode"] != 0:
        return []

    return [
        x.strip()
        for x in result["stdout"].splitlines()
        if x.strip()
    ]

# ============================================================
# MAC APP STORE
# ============================================================

def get_mas_apps():
    if not shutil.which("mas"):
        return []

    result = run_command("mas list")

    if result["returncode"] != 0:
        return []

    apps = []

    for line in result["stdout"].splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            apps.append({
                "id": parts[0],
                "name": parts[1],
                "version": parts[2]
            })

    return apps

# ============================================================
# SAVE FILE
# ============================================================

def save_text(context, filename, content):
    path = context.config / "applications" / filename
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    if hasattr(context, 'register_artifact'):
        context.register_artifact(path)
        
    return path

# ============================================================
# MAIN
# ============================================================

def backup(context): # Rinominato da run() a backup() per matchare il plugin loader
    result: dict = {
        "installed_apps": [],
        "brew_casks": [],
        "mac_app_store": []
    }

    result["installed_apps"] = scan_applications()
    result["brew_casks"] = get_brew_casks()
    result["mac_app_store"] = get_mas_apps()

    f1 = save_text(
        context,
        "applications.txt",
        "\n".join([f'{x["name"]} {x.get("version") or ""}' for x in result["installed_apps"]])
    )

    f2 = save_text(
        context,
        "brew-casks.txt",
        "\n".join(result["brew_casks"])
    )

    if result["mac_app_store"]:
        f3 = save_text(
            context,
            "mas-apps.txt",
            "\n".join([f'{x["id"]}\t{x["name"]}\t{x["version"]}' for x in result["mac_app_store"]])
        )

    result["summary"] = {
        "total_apps": len(result["installed_apps"]),
        "brew_casks": len(result["brew_casks"]),
        "mas_apps": len(result["mac_app_store"])
    }

    inventory_file = save_inventory(context, "applications", result)
    print(
        "Application inventory completed: "
        f"{result['summary']['total_apps']} apps, "
        f"{result['summary']['brew_casks']} Homebrew casks and "
        f"{result['summary']['mas_apps']} App Store apps recorded."
    )

    return result
