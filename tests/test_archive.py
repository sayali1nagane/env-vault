"""Tests for env_vault.archive."""

from __future__ import annotations

import tarfile
from pathlib import Path

import pytest

from env_vault.crypto import generate_key
from env_vault.storage import init_vault_dir, write_vault, get_vault_path, get_meta_path
from env_vault.archive import (
    create_archive,
    restore_archive,
    list_archives,
    delete_archive,
)


@pytest.fixture()
def populated_vault(tmp_path: Path):
    key = generate_key()
    init_vault_dir(tmp_path, "default")
    write_vault(tmp_path, b"encrypted-data", "default")
    meta = get_meta_path(tmp_path, "default")
    meta.write_text('{"created": "2024-01-01"}')
    return tmp_path, key


def test_create_archive_returns_path(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default")
    assert dest.exists()
    assert dest.suffix == ".gz"


def test_create_archive_is_valid_tar(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default")
    assert tarfile.is_tarfile(dest)


def test_create_archive_contains_enc_file(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default")
    with tarfile.open(dest, "r:gz") as tar:
        names = tar.getnames()
    assert "default.enc" in names


def test_create_archive_contains_meta_file(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default")
    with tarfile.open(dest, "r:gz") as tar:
        names = tar.getnames()
    assert "default.meta.json" in names


def test_create_archive_custom_name(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default", name="my-backup")
    assert dest.name == "my-backup.tar.gz"


def test_create_archive_raises_if_vault_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        create_archive(tmp_path, "nonexistent")


def test_restore_archive_recreates_vault(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default", name="backup1")
    get_vault_path(base, "default").unlink()
    restored = restore_archive(base, dest)
    assert restored == "default"
    assert get_vault_path(base, "default").exists()


def test_restore_archive_with_profile_override(populated_vault):
    base, _ = populated_vault
    dest = create_archive(base, "default", name="backup2")
    restored = restore_archive(base, dest, profile="staging")
    assert restored == "staging"
    assert get_vault_path(base, "staging").exists()


def test_restore_raises_if_archive_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_archive(tmp_path, tmp_path / "ghost.tar.gz")


def test_list_archives_empty_when_none(tmp_path):
    assert list_archives(tmp_path) == []


def test_list_archives_returns_entries(populated_vault):
    base, _ = populated_vault
    create_archive(base, "default", name="arc1")
    create_archive(base, "default", name="arc2")
    entries = list_archives(base)
    names = [e["name"] for e in entries]
    assert "arc1" in names
    assert "arc2" in names


def test_delete_archive_removes_file(populated_vault):
    base, _ = populated_vault
    create_archive(base, "default", name="to-delete")
    delete_archive(base, "to-delete")
    archives_dir = base / ".env-vault" / "archives"
    assert not (archives_dir / "to-delete.tar.gz").exists()


def test_delete_archive_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        delete_archive(tmp_path, "ghost")
