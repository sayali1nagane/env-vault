"""Tests for env_vault.storage module."""

import pytest
from pathlib import Path

from env_vault.storage import (
    get_vault_dir,
    get_vault_path,
    get_meta_path,
    init_vault_dir,
    write_vault,
    read_vault,
    write_meta,
    read_meta,
    vault_exists,
    DEFAULT_VAULT_DIR,
)


def test_get_vault_dir_uses_base_path(tmp_path):
    vault_dir = get_vault_dir(tmp_path)
    assert vault_dir == tmp_path / DEFAULT_VAULT_DIR


def test_get_vault_path_returns_enc_file(tmp_path):
    vault_path = get_vault_path(tmp_path)
    assert vault_path.suffix == ".enc"
    assert vault_path.parent == get_vault_dir(tmp_path)


def test_get_meta_path_returns_json_file(tmp_path):
    meta_path = get_meta_path(tmp_path)
    assert meta_path.suffix == ".json"


def test_init_vault_dir_creates_directory(tmp_path):
    vault_dir = init_vault_dir(tmp_path)
    assert vault_dir.exists()
    assert vault_dir.is_dir()


def test_write_and_read_vault(tmp_path):
    data = b"encrypted_data_bytes"
    write_vault(data, tmp_path)
    result = read_vault(tmp_path)
    assert result == data


def test_read_vault_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_vault(tmp_path)


def test_write_and_read_meta(tmp_path):
    meta = {"version": 1, "created_at": "2024-01-01", "key_id": "abc123"}
    write_meta(meta, tmp_path)
    result = read_meta(tmp_path)
    assert result == meta


def test_read_meta_returns_empty_dict_if_missing(tmp_path):
    result = read_meta(tmp_path)
    assert result == {}


def test_vault_exists_false_before_write(tmp_path):
    assert not vault_exists(tmp_path)


def test_vault_exists_true_after_write(tmp_path):
    write_vault(b"some data", tmp_path)
    assert vault_exists(tmp_path)
