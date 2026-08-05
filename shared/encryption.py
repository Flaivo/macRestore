"""Encryption helpers for complete Mac Restore backup archives."""

import base64
import json
import os
import shutil
import tarfile
import tempfile
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


MAGIC = b"MACRESTORE-ENCRYPTED-BACKUP\n"
SALT_SIZE = 16
NONCE_SIZE = 12
TAG_SIZE = 16
MIN_PASSWORD_LENGTH = 8


def is_encrypted_backup(path):
    return Path(path).is_file() and Path(path).suffix == ".backup"


def _key_from_password(password, salt):
    if not password:
        raise ValueError("Backup password cannot be empty")
    return Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1,
    ).derive(password.encode("utf-8"))


def validate_backup_password(password):
    """Validate the user-facing password policy for new encrypted backups."""
    if not password:
        raise ValueError("Backup password cannot be empty")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters"
        )
    if not any(character.isupper() for character in password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(character.islower() for character in password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(character.isdigit() for character in password):
        raise ValueError("Password must contain at least one number")
    if not any(not character.isalnum() and not character.isspace() for character in password):
        raise ValueError("Password must contain at least one special symbol")


def _write_header(output, salt, nonce, archive_name):
    header = {
        "version": 1,
        "algorithm": "AES-256-GCM",
        "kdf": "scrypt",
        "salt": base64.b64encode(salt).decode("ascii"),
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "archive": archive_name,
    }
    output.write(MAGIC)
    output.write(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    output.write(b"\n")


def encrypt_backup_directory(source_dir, encrypted_path, password):
    validate_backup_password(password)
    source_dir = Path(source_dir).resolve()
    encrypted_path = Path(encrypted_path).resolve()
    if not source_dir.is_dir():
        raise ValueError(f"Backup not found: {source_dir}")

    encrypted_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_archive = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="macrestore-", suffix=".tar.gz", delete=False
        ) as archive_file:
            temporary_archive = Path(archive_file.name)

        with tarfile.open(temporary_archive, "w:gz") as archive:
            archive.add(source_dir, arcname=source_dir.name, recursive=True)

        salt = os.urandom(SALT_SIZE)
        nonce = os.urandom(NONCE_SIZE)
        key = _key_from_password(password, salt)
        encryptor = Cipher(
            algorithms.AES(key), modes.GCM(nonce)
        ).encryptor()

        temporary_output = encrypted_path.with_suffix(encrypted_path.suffix + ".tmp")
        try:
            with temporary_archive.open("rb") as source, temporary_output.open("wb") as output:
                _write_header(output, salt, nonce, temporary_archive.name)
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(encryptor.update(chunk))
                output.write(encryptor.finalize())
                output.write(encryptor.tag)
            os.replace(temporary_output, encrypted_path)
        finally:
            temporary_output.unlink(missing_ok=True)
    finally:
        if temporary_archive:
            temporary_archive.unlink(missing_ok=True)

    return encrypted_path


def _read_header(source):
    if source.readline() != MAGIC:
        raise ValueError("Unrecognized encrypted backup format")
    try:
        header = json.loads(source.readline().decode("utf-8"))
        salt = base64.b64decode(header["salt"])
        nonce = base64.b64decode(header["nonce"])
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Invalid encrypted backup header") from error
    if len(salt) != SALT_SIZE or len(nonce) != NONCE_SIZE:
        raise ValueError("Invalid cryptographic parameters")
    return salt, nonce


def _safe_extract(archive, destination):
    destination = destination.resolve()
    for member in archive.getmembers():
        if member.name.startswith("/"):
            raise ValueError("Archive contains an invalid absolute path")
        target = (destination / member.name).resolve()
        try:
            target.relative_to(destination)
        except ValueError as error:
            raise ValueError("Archive contains a path outside the destination") from error
        if member.issym() or member.islnk():
            raise ValueError("Archive contains an unsupported link")
    archive.extractall(destination)


@contextmanager
def decrypted_backup(encrypted_path, password):
    encrypted_path = Path(encrypted_path).resolve()
    if not encrypted_path.is_file():
        raise ValueError(f"Encrypted backup not found: {encrypted_path}")

    temporary_root = Path(tempfile.mkdtemp(prefix=".macrestore-decrypted-"))
    temporary_root.chmod(0o700)
    temporary_archive = temporary_root / "backup.tar.gz"
    try:
        with encrypted_path.open("rb") as source:
            salt, nonce = _read_header(source)
            cipher_length = encrypted_path.stat().st_size - source.tell() - TAG_SIZE
            if cipher_length < 0:
                raise ValueError("Encrypted backup is truncated")
            decryptor = Cipher(
                algorithms.AES(_key_from_password(password, salt)),
                modes.GCM(nonce),
            ).decryptor()
            with temporary_archive.open("wb") as output:
                remaining = cipher_length
                while remaining:
                    chunk = source.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ValueError("Encrypted backup is truncated")
                    output.write(decryptor.update(chunk))
                    remaining -= len(chunk)
                tag = source.read(TAG_SIZE)
                if len(tag) != TAG_SIZE:
                    raise ValueError("Encrypted backup has no authentication tag")
                try:
                    output.write(decryptor.finalize_with_tag(tag))
                except Exception as error:
                    raise ValueError("Incorrect password or modified encrypted backup") from error

        with tarfile.open(temporary_archive, "r:gz") as archive:
            _safe_extract(archive, temporary_root)
        extracted = [
            item for item in temporary_root.iterdir()
            if item != temporary_archive
        ]
        if len(extracted) != 1 or not extracted[0].is_dir():
            raise ValueError("Invalid encrypted backup structure")
        yield extracted[0]
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
