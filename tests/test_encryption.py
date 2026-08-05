from pathlib import Path

import pytest

from shared.encryption import (
    decrypted_backup,
    encrypt_backup_directory,
    is_encrypted_backup,
    validate_backup_password,
)


def test_encrypted_backup_round_trip(tmp_path: Path):
    source = tmp_path / "backup"
    source.mkdir()
    (source / "manifest.json").write_text("{}", encoding="utf-8")
    (source / "files.txt").write_text("sensitive", encoding="utf-8")
    encrypted = tmp_path / "backup.backup"

    encrypt_backup_directory(source, encrypted, "Correct horse1!")

    assert is_encrypted_backup(encrypted)
    with decrypted_backup(encrypted, "Correct horse1!") as restored:
        assert (restored / "manifest.json").read_text() == "{}"
        assert (restored / "files.txt").read_text() == "sensitive"


def test_encrypted_backup_rejects_wrong_password(tmp_path: Path):
    source = tmp_path / "backup"
    source.mkdir()
    (source / "data.txt").write_text("secret", encoding="utf-8")
    encrypted = tmp_path / "backup.backup"
    encrypt_backup_directory(source, encrypted, "Correct horse1!")

    with pytest.raises(ValueError, match="Incorrect password"):
        with decrypted_backup(encrypted, "Wrong password2!"):
            pass


@pytest.mark.parametrize(
    "password",
    ["aB3!xyz", "abcdefgh!", "ABCDEFGH1!", "Abcdefgh!"],
)
def test_new_backup_password_requires_all_character_classes(password):
    with pytest.raises(ValueError):
        validate_backup_password(password)


def test_new_backup_password_accepts_requested_policy():
    validate_backup_password("Abcdef1!")
