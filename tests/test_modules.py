from audit.modules.obsidian import ignore_bloat
from audit.modules.disk_usage import PLUGIN as disk_usage_plugin
from audit.modules.vmware import inspect_bundle
from audit.engine import AuditEngine
from shared.filesystem import create_temporary_backup_directory
import stat
import json
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
