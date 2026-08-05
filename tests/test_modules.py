from audit.modules.obsidian import ignore_bloat
from audit.modules.disk_usage import PLUGIN as disk_usage_plugin
from audit.modules.vmware import inspect_bundle
from audit.engine import AuditEngine
from shared.filesystem import create_temporary_backup_directory
import stat


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
