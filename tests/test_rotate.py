"""Tests for env_vault.rotate module."""

import pytest
from pathlib import Path

from env_vault.crypto import generate_key, encrypt, decrypt
from env_vault.storage import (
    init_vault_dir,
    write_vault,
    read_vault,
    save_key,
    load_key,
)
from env_vault.rotate import rotate_key, get_rotation_info


PROJECT = "testproject"
PLAINTEXT = b"DB_HOST=localhost\nDB_PASS=secret\n"


@pytest.fixture
def populated_vault(tmp_path):
    key = generate_key()
    init_vault_dir(PROJECT, tmp_path)
    ciphertext = encrypt(PLAINTEXT, key)
    write_vault(PROJECT, tmp_path, ciphertext)
    save_key(PROJECT, tmp_path, key)
    return tmp_path, key


def test_rotate_key_returns_new_key(populated_vault):
    base_path, old_key = populated_vault
    new_key = rotate_key(PROJECT, base_path)
    assert isinstance(new_key, bytes)
    assert new_key != old_key


def test_rotate_key_data_still_decryptable(populated_vault):
    base_path, _ = populated_vault
    new_key = rotate_key(PROJECT, base_path)
    ciphertext = read_vault(PROJECT, base_path)
    recovered = decrypt(ciphertext, new_key)
    assert recovered == PLAINTEXT


def test_rotate_key_old_key_no_longer_works(populated_vault):
    base_path, old_key = populated_vault
    rotate_key(PROJECT, base_path)
    ciphertext = read_vault(PROJECT, base_path)
    with pytest.raises(Exception):
        decrypt(ciphertext, old_key)


def test_rotate_key_saves_new_key_to_storage(populated_vault):
    base_path, old_key = populated_vault
    new_key = rotate_key(PROJECT, base_path)
    stored_key = load_key(PROJECT, base_path)
    assert stored_key == new_key
    assert stored_key != old_key


def test_rotate_key_raises_if_vault_missing(tmp_path):
    init_vault_dir(PROJECT, tmp_path)
    with pytest.raises(FileNotFoundError, match="Vault not found"):
        rotate_key(PROJECT, tmp_path)


def test_rotate_key_updates_meta_last_rotated(populated_vault):
    base_path, _ = populated_vault
    rotate_key(PROJECT, base_path)
    info = get_rotation_info(PROJECT, base_path)
    assert info["last_rotated"] is not None


def test_get_rotation_info_no_meta(tmp_path):
    init_vault_dir(PROJECT, tmp_path)
    info = get_rotation_info(PROJECT, tmp_path)
    assert info["last_rotated"] is None


def test_rotate_key_with_explicit_old_key(populated_vault):
    base_path, old_key = populated_vault
    new_key = rotate_key(PROJECT, base_path, old_key=old_key)
    ciphertext = read_vault(PROJECT, base_path)
    recovered = decrypt(ciphertext, new_key)
    assert recovered == PLAINTEXT
