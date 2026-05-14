"""Tests for profile management module and CLI."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from env_vault.profile import (
    list_profiles,
    get_active_profile,
    set_active_profile,
    copy_profile,
    delete_profile,
    DEFAULT_PROFILE,
)
from env_vault.crypto import generate_key, encrypt
from env_vault.cli_profile import profile_group


@pytest.fixture
def tmp_base(tmp_path):
    vault_dir = tmp_path / ".env-vault"
    vault_dir.mkdir()
    return tmp_path


@pytest.fixture
def populated_base(tmp_base):
    key = generate_key()
    vault_dir = tmp_base / ".env-vault"
    for name in ["default", "staging"]:
        ciphertext = encrypt(b"KEY=value", key)
        (vault_dir / f"{name}.enc").write_bytes(ciphertext)
    (vault_dir / ".key").write_bytes(key)
    return tmp_base, key


def test_list_profiles_empty(tmp_base):
    profiles = list_profiles(tmp_base)
    assert profiles == []


def test_list_profiles_returns_names(populated_base):
    base, _ = populated_base
    profiles = list_profiles(base)
    assert "default" in profiles
    assert "staging" in profiles


def test_get_active_profile_defaults_to_default(tmp_base):
    assert get_active_profile(tmp_base) == DEFAULT_PROFILE


def test_set_and_get_active_profile(tmp_base):
    set_active_profile(tmp_base, "staging")
    assert get_active_profile(tmp_base) == "staging"


def test_set_active_profile_persists_json(tmp_base):
    set_active_profile(tmp_base, "prod")
    meta = json.loads((tmp_base / ".env-vault" / "profiles.json").read_text())
    assert meta["active"] == "prod"


def test_copy_profile_creates_new_vault(populated_base):
    base, key = populated_base
    copy_profile(base, "default", "prod", key)
    assert (base / ".env-vault" / "prod.enc").exists()


def test_copy_profile_missing_src_raises(tmp_base):
    key = generate_key()
    with pytest.raises(FileNotFoundError):
        copy_profile(tmp_base, "nonexistent", "new", key)


def test_delete_profile_removes_file(populated_base):
    base, _ = populated_base
    delete_profile(base, "staging")
    assert not (base / ".env-vault" / "staging.enc").exists()


def test_delete_default_profile_raises(populated_base):
    base, _ = populated_base
    with pytest.raises(ValueError):
        delete_profile(base, "default")


def test_cli_list_shows_active(populated_base):
    base, _ = populated_base
    set_active_profile(base, "staging")
    runner = CliRunner()
    result = runner.invoke(profile_group, ["list", "--base", str(base)])
    assert result.exit_code == 0
    assert "staging (active)" in result.output


def test_cli_use_switches_profile(populated_base):
    base, _ = populated_base
    runner = CliRunner()
    result = runner.invoke(profile_group, ["use", "staging", "--base", str(base)])
    assert result.exit_code == 0
    assert get_active_profile(base) == "staging"


def test_cli_use_missing_profile_fails(tmp_base):
    runner = CliRunner()
    result = runner.invoke(profile_group, ["use", "ghost", "--base", str(tmp_base)])
    assert result.exit_code != 0
