import shutil
from pathlib import Path

PLUGIN = {
    "name": "vpn",
    "description": "Estrae i profili VPN (.tblk, .ovpn) sulla Scrivania per la reinstallazione"
}

def restore(context):
    source_dir = context.files_dir / "vpn"
    dest_dir = Path.home() / "Desktop" / "VPN_Ripristinate"

    if not source_dir.exists() or not any(source_dir.iterdir()):
        print("  ⏭️  Nessun profilo VPN trovato, salto.")
        return

    # LOGICA DRY-RUN
    if context.dry_run:
        print(f"  [DRY-RUN] Creerei la cartella {dest_dir}")
        for file_path in source_dir.iterdir():
            if file_path.name != ".DS_Store":
                print(f"  [DRY-RUN] Metterei il profilo '{file_path.name}' sulla Scrivania")
        return

    # LOGICA REALE
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
        print(f"  ✅ Profili VPN estratti e pronti in: {dest_dir}")
        print("  💡 NOTA: Fai doppio clic sui file .tblk per reimportarli in Tunnelblick.")
    except Exception as e:
        print(f"  ❌ Errore nel ripristino VPN: {e}")
