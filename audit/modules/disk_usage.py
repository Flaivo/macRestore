import subprocess
from pathlib import Path
from shared.inventory import save_inventory

PLUGIN = {
    "name": "disk_usage",
    "description": "Analisi utilizzo disco e ricerca file pesanti (System Data)",
    "requires_password": False,
    "has_restore": False,
    "restore_items": []
}

def run_cmd(cmd):
    """Esegue un comando shell e ne restituisce l'output, ignorando gli errori di permessi."""
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""

def backup(context):
    result = {}
    report_lines = []

    print("Analisi del disco in corso (potrebbe richiedere qualche secondo)...")

    # ============================================================
    # 1. PANORAMICA DISCO
    # ============================================================
    report_lines.append("=== PANORAMICA DISCO DI SISTEMA ===")
    df_out = run_cmd("df -h /")
    report_lines.append(df_out)
    report_lines.append("")

    # ============================================================
    # 2. SNAPSHOT LOCALI TIME MACHINE
    # Spesso occupano decine di GB di "Dati di sistema" fantasma
    # ============================================================
    report_lines.append("=== SNAPSHOT LOCALI TIME MACHINE (Spazio nascosto) ===")
    tm_out = run_cmd("tmutil listlocalsnapshots /")
    report_lines.append(tm_out if tm_out else "Nessuno snapshot locale trovato.")
    report_lines.append("")

    # ============================================================
    # 3. CARTELLE UTENTE PRINCIPALI
    # ============================================================
    report_lines.append("=== DIMENSIONE CARTELLE PRINCIPALI UTENTE ===")
    dirs_to_check = [
        "~/Library", 
        "~/Documents", 
        "~/Downloads", 
        "~/Desktop", 
        "~/Developer", 
        "~/Projects"
    ]
    for d in dirs_to_check:
        size = run_cmd(f"du -sh {d} 2>/dev/null")
        if size:
            report_lines.append(size)
    report_lines.append("")

    # ============================================================
    # 4. TOP 15 CARTELLE PIU' PESANTI IN ~/Library
    # Qui è dove si nascondono Simulatori, Cache, DerivedData, ecc.
    # ============================================================
    report_lines.append("=== TOP 15 CARTELLE PIU' PESANTI NELLA LIBRERIA (~/Library) ===")
    # du -sm calcola in Megabyte per poter ordinare numericamente (sort -nr)
    top_lib = run_cmd("du -sm ~/Library/* 2>/dev/null | sort -nr | head -15")
    
    for line in top_lib.splitlines():
        parts = line.split('\t')
        if len(parts) == 2:
            mb = int(parts[0])
            gb = mb / 1024
            path = parts[1].replace(str(Path.home()), "~")
            
            # Formatta in GB se supera 1GB, altrimenti MB
            if gb > 1:
                report_lines.append(f"{gb:.2f} GB\t{path}")
            else:
                report_lines.append(f"{mb} MB\t{path}")

    # ============================================================
    # SALVATAGGIO REPORT
    # ============================================================
    report_content = "\n".join(report_lines)
    
    # Questo va in config perché è solo un file di testo (log)
    dest_dir = context.config / "disk_usage"
    dest_dir.mkdir(parents=True, exist_ok=True)
    report_file = dest_dir / "disk_report.txt"
    report_file.write_text(report_content, encoding="utf-8")

    result["report_generated"] = True
    result["report_path"] = str(report_file.relative_to(context.config.parent))

    print(f"Analisi disco completata. Risultati salvati in: {report_file.name}")

    if hasattr(context, 'register_artifact'):
        context.register_artifact(dest_dir)

    save_inventory(context, "disk_usage", result)
    return result
