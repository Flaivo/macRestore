from audit.modules.obsidian import ignore_bloat
from audit.modules.disk_usage import PLUGIN as disk_usage_plugin
from audit.modules.vmware import inspect_bundle
from audit.engine import AuditEngine
from shared.filesystem import create_temporary_backup_directory
import stat
import json
import subprocess
import audit.engine as audit_engine_module
from shared.manifest import create_manifest
from shared.report import create_backup_report
from shared.report import create_restore_report
from shared.encryption import decrypted_backup


def test_obsidian_ignores_runtime_files():
    names = ["SingletonSocket", "SingletonCookie", "SingletonLock", "obsidian.json"]

    ignored = ignore_bloat(None, names)

    assert set(ignored) == {"SingletonSocket", "SingletonCookie", "SingletonLock"}


def test_vmware_inventory_does_not_copy_virtual_disk(tmp_path):
    bundle = tmp_path / "Windows.vmwarevm"
    bundle.mkdir()
    (bundle / "Windows.vmx").write_text("config.version = \"8\"", encoding="utf-8")
    (bundle / "Windows.vmdk").write_bytes(b"virtual disk placeholder")

    result = inspect_bundle(bundle)

    assert result["exists"] is True
    assert result["vmx_files"] == ["Windows.vmx"]
    assert result["disk_contents_backed_up_by_macrestore"] is False


def test_disk_usage_is_optional_for_default_backup_selection():
    assert disk_usage_plugin["default_enabled"] is False


def test_system_printer_inventory_parses_cups_output(monkeypatch):
    import audit.modules.system as system_audit

    outputs = {
        "lpstat -v": "device for Office Printer: ipps://printer.local/ipp/print\n",
        "lpstat -p": "printer Office Printer is idle. enabled since Tue 16 Sep 2026\n",
        "lpstat -l -p": "printer Office Printer is idle.\n\tInterface: Xerox VersaLink C405\n",
        "lpstat -d": "system default destination: Office Printer\n",
    }
    monkeypatch.setattr(
        system_audit,
        "run",
        lambda command: {"stdout": outputs[command], "success": True},
    )

    result = system_audit._printer_inventory()

    assert result["default_printer"] == "Office Printer"
    assert result["printers"][0]["name"] == "Office Printer"
    assert result["printers"][0]["device_uri"] == "ipps://printer.local/ipp/print"
    assert result["printers"][0]["is_default"] is True
    assert result["printers"][0]["interface"] == "Xerox VersaLink C405"


def test_interrupted_backup_cleanup_removes_plaintext_directory(tmp_path):
    plaintext_backup = tmp_path / "2026-08-05_120000"
    plaintext_backup.mkdir()
    (plaintext_backup / "secret.txt").write_text("secret", encoding="utf-8")

    engine = AuditEngine()
    engine._active_plaintext_backup = plaintext_backup
    engine._cleanup_plaintext_backup()

    assert not plaintext_backup.exists()


def test_plaintext_staging_directory_is_private_and_temporary():
    staging = create_temporary_backup_directory()
    try:
        assert staging.name.startswith(".macrestore-")
        assert stat.S_IMODE(staging.stat().st_mode) == 0o700
    finally:
        staging.rmdir()


def test_backup_report_contains_module_status_inventory_and_file_metadata(tmp_path):
    (tmp_path / "inventory").mkdir()
    (tmp_path / "files").mkdir()
    (tmp_path / "files" / "secret.txt").write_text("secret", encoding="utf-8")
    (tmp_path / "inventory" / "demo.json").write_text(
        json.dumps({"module": "demo", "data": {"files": [{
            "source": "~/secret.txt",
            "backup": "files/secret.txt",
            "restore_to": "~/secret.txt",
        }]}}),
        encoding="utf-8",
    )
    manifest = create_manifest({"demo": {"status": "success", "artifacts": ["files/secret.txt"]}})

    report = create_backup_report(tmp_path, manifest)
    content = report.read_text(encoding="utf-8")

    assert "ATTENZIONE" not in content
    assert "~/secret.txt" in content
    assert "files/secret.txt" in content
    assert "Size" in content
    assert "Detailed inventories" in content


def test_audit_creates_external_text_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_engine_module, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(
        audit_engine_module.getpass,
        "getpass",
        lambda prompt: "ValidPass1!",
    )

    encrypted = audit_engine_module.AuditEngine().run(selected=["system"])
    assert encrypted is not None
    report = encrypted.with_suffix(".txt")

    assert encrypted.exists()
    assert report.exists()
    summary = report.read_text(encoding="utf-8")
    assert "Overall result" in summary
    assert "secret.txt" not in summary
    with decrypted_backup(encrypted, "ValidPass1!") as decrypted:
        assert (decrypted / "backup_report.md").exists()


def test_restore_dry_run_creates_report(tmp_path):
    from restore.engine import RestoreEngine

    for folder in ("inventory", "backup_config", "files"):
        (tmp_path / folder).mkdir()
    report = tmp_path.parent / "restore-test.txt"
    results = RestoreEngine(tmp_path, dry_run=True, report_path=report).run(selected=["browser"])

    assert results[0]["status"] == "skipped"
    assert report.exists()
    content = report.read_text(encoding="utf-8")
    assert "DRY-RUN (no files changed)" in content
    assert "browser" in content


def test_mysql_restore_generates_secure_import_script(tmp_path, monkeypatch):
    import restore.modules.mysql as mysql_restore
    from restore.engine import RestoreContext
    from pathlib import Path

    fake_home = tmp_path / "home"
    source = tmp_path / "backup" / "files" / "mysql"
    source.mkdir(parents=True)
    (source / "example.sql.gz").write_bytes(b"compressed dump")
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    mysql_restore.restore(RestoreContext(tmp_path / "backup", dry_run=False))

    output = fake_home / "Desktop" / "Database_Restored"
    script = output / "restore_mysql.sh"
    assert script.exists()
    assert stat.S_IMODE(script.stat().st_mode) == 0o700
    content = script.read_text(encoding="utf-8")
    assert "CREATE DATABASE IF NOT EXISTS example;" in content
    assert '"$SCRIPT_DIR"/example.sql.gz' in content
    assert "MYSQL_ROOT_PASSWORD" in content
    assert "password=" in content
    assert "compressed dump" not in content
    syntax = subprocess.run(["sh", "-n", str(script)], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr


def test_system_lists_generates_application_download_sources(tmp_path, monkeypatch):
    import restore.modules.system_lists as system_lists_restore
    from restore.engine import RestoreContext
    from pathlib import Path

    fake_home = tmp_path / "home"
    backup = tmp_path / "backup"
    (backup / "backup_config" / "applications").mkdir(parents=True)
    (backup / "backup_config" / "applications" / "applications.txt").write_text(
        "MySQLWorkbench 8.0.43.CE\nSystem Settings 1.0\n", encoding="utf-8"
    )
    (backup / "backup_config" / "homebrew").mkdir(parents=True)
    (backup / "backup_config" / "homebrew" / "Brewfile").write_text(
        'brew "wget"\n', encoding="utf-8"
    )
    (backup / "inventory").mkdir()
    (backup / "inventory" / "applications.json").write_text(
        json.dumps({
            "data": {
                "installed_apps": [
                    {"name": "MySQLWorkbench", "version": "8.0.43.CE"},
                    {"name": "System Settings", "version": "1.0"},
                    {"name": "Unknown Tool", "version": "2.0"},
                ],
                "brew_casks": ["zulu@17"],
            }
        }),
        encoding="utf-8",
    )
    (backup / "inventory" / "system.json").write_text(
        json.dumps({
            "data": {
                "printers": {
                    "default_printer": "Office Printer",
                    "printers": [{
                        "name": "Office Printer",
                        "device_uri": "ipps://printer.local/ipp/print",
                        "status": "idle. enabled",
                        "is_default": True,
                    }, {
                        "name": "Zebra ZD421",
                        "device_uri": "ipp://zebra.local/ipp/print",
                        "status": "idle. enabled",
                        "is_default": False,
                    }, {
                        "name": "Canon Office",
                        "device_uri": "ipp://canon.local/ipp/print",
                        "status": "idle. enabled",
                        "is_default": False,
                    }, {
                        "name": "Xerox Office",
                        "device_uri": "ipp://xerox.local/ipp/print",
                        "status": "idle. enabled",
                        "is_default": False,
                    }],
                }
            }
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    system_lists_restore.restore(RestoreContext(backup, dry_run=False))

    output = fake_home / "Desktop" / "Install_Lists" / "APPLICATION_DOWNLOADS.md"
    content = output.read_text(encoding="utf-8")
    assert "https://dev.mysql.com/downloads/mysql/" in content
    assert "https://dev.mysql.com/downloads/workbench/" in content
    assert "System Settings" not in content
    assert "Unknown Tool" in content
    assert "zulu@17" in content

    printer_guide = output.parent / "PRINTERS.md"
    printer_script = output.parent / "restore_printers.sh"
    assert "Office Printer" in printer_guide.read_text(encoding="utf-8")
    assert printer_script.exists()
    assert stat.S_IMODE(printer_script.stat().st_mode) == 0o700
    printer_syntax = subprocess.run(["sh", "-n", str(printer_script)], capture_output=True, text=True)
    assert printer_syntax.returncode == 0, printer_syntax.stderr
    assert "lpadmin" in printer_script.read_text(encoding="utf-8")
    printer_script_content = printer_script.read_text(encoding="utf-8")
    assert "https://www.zebra.com/us/en/support-downloads/printers.html" in printer_script_content
    assert "https://www.usa.canon.com/support/software-and-drivers" in printer_script_content
    assert "https://www.support.xerox.com/en-us" in printer_script_content
    assert "Select a queue (one at a time)" in printer_script_content

    parent_guide = output.parent / "RESTORE_GUIDE.md"
    guide_content = parent_guide.read_text(encoding="utf-8")
    assert "does not clone repositories or restore tracked source code" in guide_content
    assert "Reinstall project dependencies" in guide_content

    install_list = output.parent / "applications.txt"
    full_list = output.parent / "applications-full.txt"
    assert "MySQLWorkbench 8.0.43.CE" in install_list.read_text(encoding="utf-8")
    assert "System Settings" not in install_list.read_text(encoding="utf-8")
    assert "System Settings" in full_list.read_text(encoding="utf-8")

    commands = output.parent / "INSTALL_COMMANDS.sh"
    assert commands.exists()
    assert stat.S_IMODE(commands.stat().st_mode) == 0o700
    syntax = subprocess.run(["sh", "-n", str(commands)], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr


def test_mobile_dev_avd_backup_and_restore(tmp_path, monkeypatch):
    import audit.modules.mobile_dev as mobile_dev_audit
    import restore.modules.mobile_dev as mobile_dev_restore
    from shared.context import BackupContext
    from restore.engine import RestoreContext
    from pathlib import Path

    fake_home = tmp_path / "home"
    fake_android = fake_home / ".android" / "avd"
    fake_android.mkdir(parents=True)

    # Crea mock AVD
    (fake_android / "Pixel_7_API_34.ini").write_text(
        "path=/old/path/.android/avd/Pixel_7_API_34.avd\ntarget=android-34\n",
        encoding="utf-8"
    )
    avd_folder = fake_android / "Pixel_7_API_34.avd"
    avd_folder.mkdir()
    (avd_folder / "config.ini").write_text(
        "hw.device.name=pixel_7\nimage.sysdir.1=system-images/android-34/google_apis/arm64-v8a/\nabi.type=arm64-v8a\n",
        encoding="utf-8"
    )
    # File disco finto che NON deve essere copiato
    (avd_folder / "userdata.img").write_bytes(b"dummy image data")

    monkeypatch.setattr(Path, "home", lambda: fake_home)

    # Esegui Backup
    backup_dir = tmp_path / "backup"
    ctx = BackupContext(backup_dir)
    ctx.prepare()
    ctx.set_module("mobile_dev")

    result = mobile_dev_audit.backup(ctx)

    assert len(result["android_avds"]) == 1
    assert result["android_avds"][0]["name"] == "Pixel_7_API_34"
    assert result["android_avds"][0]["device_name"] == "pixel_7"
    assert not (backup_dir / "files" / "mobile_dev" / "android_avd" / "Pixel_7_API_34.avd" / "userdata.img").exists()
    # Verifica che le istruzioni/script siano DENTRO il backup (files/mobile_dev)
    assert (backup_dir / "files" / "mobile_dev" / "recreate_emulators.sh").exists()
    assert (backup_dir / "files" / "mobile_dev" / "recreate_emulators.md").exists()

    # Esegui Restore
    new_home = tmp_path / "new_home"
    monkeypatch.setattr(Path, "home", lambda: new_home)

    restore_ctx = RestoreContext(backup_dir, dry_run=False)
    mobile_dev_restore.restore(restore_ctx)

    restored_ini = new_home / ".android" / "avd" / "Pixel_7_API_34.ini"
    assert restored_ini.exists()
    ini_content = restored_ini.read_text(encoding="utf-8")
    assert str(new_home / ".android" / "avd" / "Pixel_7_API_34.avd") in ini_content

    recreate_sh = new_home / ".android" / "recreate_emulators.sh"
    assert recreate_sh.exists()
    sh_content = recreate_sh.read_text(encoding="utf-8")
    assert "avdmanager create avd" in sh_content
    assert "Pixel_7_API_34" in sh_content


def test_mobile_dev_ios_simulators_backup(tmp_path, monkeypatch):
    import audit.modules.mobile_dev as mobile_dev_audit
    from shared.context import BackupContext
    from pathlib import Path
    import shutil

    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/xcrun" if cmd == "xcrun" else None)

    mock_simctl_output = json.dumps({
        "devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-17-4": [
                {
                    "name": "iPhone 15 Pro",
                    "udid": "1111-2222-3333-4444",
                    "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-15-Pro",
                    "state": "Shutdown",
                    "isAvailable": True
                }
            ]
        }
    })

    monkeypatch.setattr(
        mobile_dev_audit,
        "run_command",
        lambda cmd: {"success": True, "output": mock_simctl_output, "stdout": mock_simctl_output, "error": "", "returncode": 0}
    )

    backup_dir = tmp_path / "backup"
    ctx = BackupContext(backup_dir)
    ctx.prepare()
    ctx.set_module("mobile_dev")

    result = mobile_dev_audit.backup(ctx)

    assert len(result["ios_simulators"]) == 1
    assert result["ios_simulators"][0]["name"] == "iPhone 15 Pro"
    assert (backup_dir / "files" / "mobile_dev" / "xcode" / "simulators.json").exists()
    sh_content = (backup_dir / "files" / "mobile_dev" / "recreate_emulators.sh").read_text(encoding="utf-8")
    assert "xcrun simctl create" in sh_content
    assert "iPhone 15 Pro" in sh_content


def test_mobile_dev_restore_dry_run(tmp_path, monkeypatch):
    import restore.modules.mobile_dev as mobile_dev_restore
    from restore.engine import RestoreContext
    from pathlib import Path

    backup_dir = tmp_path / "backup"
    files_dir = backup_dir / "files" / "mobile_dev"
    files_dir.mkdir(parents=True)
    (files_dir / "recreate_emulators.sh").write_text("#!/bin/sh\necho test\n", encoding="utf-8")

    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    restore_ctx = RestoreContext(backup_dir, dry_run=True)
    mobile_dev_restore.restore(restore_ctx)

    # In dry-run, nessun file deve essere creato in fake_home
    assert not (fake_home / ".android").exists()


def test_audit_mobile_dev_end_to_end_encrypted(tmp_path, monkeypatch):
    monkeypatch.setattr(audit_engine_module, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(
        audit_engine_module.getpass,
        "getpass",
        lambda prompt: "ValidPass1!",
    )

    encrypted = audit_engine_module.AuditEngine().run(selected=["mobile_dev"])
    assert encrypted is not None
    assert encrypted.exists()

    with decrypted_backup(encrypted, "ValidPass1!") as decrypted:
        assert (decrypted / "manifest.json").exists()
        assert (decrypted / "inventory" / "mobile_dev.json").exists()
        assert (decrypted / "files" / "mobile_dev" / "recreate_emulators.sh").exists()
        assert (decrypted / "files" / "mobile_dev" / "recreate_emulators.md").exists()
