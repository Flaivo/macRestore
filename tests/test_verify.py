import json
from pathlib import Path

from shared.checksum import generate_checksums
from shared.verify import verify_backup


def test_backup_is_valid_when_unchanged(tmp_path: Path):
    (tmp_path / "data.txt").write_text("original", encoding="utf-8")
    generate_checksums(tmp_path)

    result = verify_backup(tmp_path)

    assert result["valid"] is True


def test_backup_detects_modified_and_extra_files(tmp_path: Path):
    (tmp_path / "data.txt").write_text("original", encoding="utf-8")
    generate_checksums(tmp_path)
    (tmp_path / "data.txt").write_text("changed", encoding="utf-8")
    (tmp_path / "unexpected.txt").write_text("extra", encoding="utf-8")

    result = verify_backup(tmp_path)

    assert result["valid"] is False
    assert {item["status"] for item in result["files"]} == {"modified", "extra"}


def test_backup_rejects_paths_outside_backup(tmp_path: Path):
    (tmp_path / "checksums.json").write_text(
        json.dumps({"../outside.txt": "irrelevant"}), encoding="utf-8"
    )

    result = verify_backup(tmp_path)

    assert result["valid"] is False
    assert result["files"][0]["status"] == "invalid_path"
