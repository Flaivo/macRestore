import os
import subprocess
from pathlib import Path
import shutil

from shared.inventory import save_inventory

PLUGIN = {
    "name": "git_ignored",
    "description": "Backup Git-ignored local files (.env, config), excluding dependencies",
    "requires_password": False,
    "has_restore": True,
    "restore_items": ["local_ignored_files"]
}

# La lista nera delle cartelle pesanti o di build che NON vogliamo salvare
EXCLUDED_DIRS = {
    "node_modules", ".next", "build", "dist", "out", 
    "android", "ios", "Pods", ".expo", ".nuxt", 
    "coverage", "target", "vendor", ".svelte-kit", 
    ".turbo", "__pycache__", ".vscode", "generated", ".prisma"
}

# File specifici inutili
EXCLUDED_FILES = {
    ".DS_Store"
}

def get_ignored_files(repo_path):
    """Interroga Git per farsi restituire l'elenco dei file ignorati."""
    try:
        cmd = ["git", "-C", str(repo_path), "ls-files", "--others", "--ignored", "--exclude-standard"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.splitlines()
    except subprocess.CalledProcessError:
        return []

def is_excluded(file_path):
    """Controlla se il file appartiene a una cartella esclusa."""
    path_parts = Path(file_path).parts
    
    if Path(file_path).name in EXCLUDED_FILES:
        return True
        
    for excluded in EXCLUDED_DIRS:
        if excluded in path_parts:
            return True
    return False

def backup(context):
    result = {
        "scanned_repos": 0,
        "backed_up_files": 0,
        "repos_with_files": []
    }

    # ============================================================
    # 1. PERCORSI DOVE CERCARE I PROGETTI
    # Aggiungi qui altre cartelle se i tuoi progetti non sono in GitHub
    # ============================================================
    search_paths = [
        Path.home() / "Documents" / "GitHub",
        Path.home() / "Developer",
        Path.home() / "Projects",
        Path.home() / "Sites"
    ]
    
    backup_base_dir = context.config.parent / "files" / "git_ignored"
    repos_found = []

    # ============================================================
    # 2. RICERCA DELLE CARTELLE .GIT (Max profondità 3)
    # ============================================================
    for base_path in search_paths:
        if not base_path.exists():
            continue
            
        print(f"Scanning projects in: {base_path} ...")
        for root, dirs, files in os.walk(base_path):
            depth = Path(root).relative_to(base_path).parts
            if len(depth) > 3:
                dirs.clear() # Evita di scendere troppo in profondità
                continue
                
            if '.git' in dirs:
                repos_found.append(Path(root))
                dirs.remove('.git') # Non entrare dentro la cartella .git stessa
                dirs.clear()        # Non scendere in sottocartelle di un repo trovato

    result["scanned_repos"] = len(repos_found)

    # ============================================================
    # 3. BACKUP SELETTIVO DEI FILE IGNORATI
    # ============================================================
    for repo in repos_found:
        ignored_files = get_ignored_files(repo)
        
        # Filtra i file scartando quelli nelle EXCLUDED_DIRS o che terminano con /
        files_to_backup = [f for f in ignored_files if not is_excluded(f) and not f.endswith('/')]
        
        if files_to_backup:
            # Mantieni la struttura delle cartelle originale (es. Documents/GitHub/mio_progetto)
            relative_repo_path = repo.relative_to(Path.home())
            repo_backup_dest = backup_base_dir / relative_repo_path
            
            backed_up_in_repo = 0
            for file_rel_path in files_to_backup:
                src_file = repo / file_rel_path
                if src_file.is_file():
                    dest_file = repo_backup_dest / file_rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dest_file)
                    backed_up_in_repo += 1
                    result["backed_up_files"] += 1
            
            if backed_up_in_repo > 0:
                result["repos_with_files"].append(str(relative_repo_path))

    if hasattr(context, 'register_artifact') and result["backed_up_files"] > 0:
        context.register_artifact(backup_base_dir)

    inventory_file = save_inventory(context, "git_ignored", result)
    print(
        "Git-ignored file backup completed: "
        f"{result['backed_up_files']} files saved across "
        f"{len(result['repos_with_files'])} repositories."
    )

    return result
