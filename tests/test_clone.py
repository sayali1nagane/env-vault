"""Tests for env_vault.clone."""

from __future__ import annotations

import pytest
from pathlib import Path

from env_vault.crypto import generate_key, encrypt, decrypt
from env_vault.storage import (
    init_vault_dir,
    write_vault,
    read_vault,
    write_meta,
    read_meta,
)
from env_vault.clone import clone_profile


@pytest.fixture()
def populated_vault(tmp_path: Path):
    """Create a minimal vault with an encrypted payload."""
    base = tmp_path / "project"
    profile = "default"
    key = generate_key()
    init_vault_dir(base, profile)
    ciphertext = encrypt(key, b"API_KEY=secret\nDEBUG=true\n")
    write_vault(base, profile, ciphertext)
    write_meta(base, profile, {"created_at": "2024-01-01T00:00:00", "profile": profile})
    return base, profile, key


def test_clone_creates_destination_vault(populated_vault, tmp_path):
    src_base, src_profile, key = populated_vault
    dst_base = tmp_path / "clone_project"
    clone_profile(src_base, dst_base, src_profile, "default")
    from env_vault.storage import get_vault_path
    assert get_vault_path(dst_base, "default").exists()


def test_clone_ciphertext_is_identical(populated_vault, tmp_path):
    src_base, src_profile, key = populated_vault
    dst_base = tmp_path / "clone_project"
    clone_profile(src_base, dst_base, src_profile, "default")
    src_ct = read_vault(src_base, src_profile)
    dst_ct = read_vault(dst_base, "default")
    assert src_ct == dst_ct


def test_clone_decryptable_with_same_key(populated_vault, tmp_path):
    src_base, src_profile, key = populated_vault
    dst_base = tmp_path / "clone_project"
    clone_profile(src_base, dst_base, src_profile, "default")
    ciphertext = read_vault(dst_base, "default")
    plaintext = decrypt(key, ciphertext)
    assert b"API_KEY=secret" in plaintext


def test_clone_copies_metadata(populated_vault, tmp_path):
    src_base, src_profile, key = populated_vault
    dst_base = tmp_path / "clone_project"
    clone_profile(src_base, dst_base, src_profile, "default")
    meta = read_meta(dst_base, "default")
    assert meta["profile"] == "default"


def test_clone_raises_if_source_missing(tmp_path):
    src_base = tmp_path / "nonexistent"
    dst_base = tmp_path / "dst"
    with pytest.raises(FileNotFoundError, match="Source vault not found"):
        clone_profile(src_base, dst_base)


def test_clone_raises_if_destination_exists(populated_vault, tmp_path):
    src_base, src_profile, key = populated_vault
    # Clone once.
    dst_base = tmp_path / "clone_project"
    clone_profile(src_base, dst_base, src_profile, "default")
    # Second clone to same destination must fail.
    with pytest.raises(FileExistsError, match="Destination vault already exists"):
        clone_profile(src_base, dst_base, src_profile, "default")


def test_clone_writes_audit_entry(populated_vault, tmp_path):
    src_base, src_profile, key = populated_vault
    dst_base = tmp_path / "clone_project"
    clone_profile(src_base, dst_base, src_profile, "default")
    from env_vault.audit import read_audit_log
    entries = read_audit_log(dst_base, "default")
    assert len(entries) == 1
    assert entries[0]["action"] == "clone"
