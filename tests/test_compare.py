"""Tests for env_vault.compare and cli_compare."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from env_vault.crypto import generate_key, save_key, encrypt
from env_vault.storage import init_vault_dir, write_vault, write_meta
from env_vault.cli_compare import compare_group


@pytest.fixture
def populated_base(tmp_path):
    """Create two profiles with known env content."""
    base = str(tmp_path)

    for profile, content in [
        ("dev", "APP_ENV=development\nDEBUG=true\nSHARED=same"),
        ("prod", "APP_ENV=production\nSECRET=hunter2\nSHARED=same"),
    ]:
        init_vault_dir(base, profile)
        key = generate_key()
        save_key(base, profile, key)
        ciphertext = encrypt(content, key)
        vault_path = Path(base) / ".env-vault" / profile / "vault.enc"
        meta_path = Path(base) / ".env-vault" / profile / "meta.json"
        write_vault(vault_path, ciphertext)
        write_meta(meta_path, {"profile": profile})

    return base


@pytest.fixture
def runner():
    return CliRunner()


def test_compare_only_in_a(populated_base):
    from env_vault.compare import compare_profiles
    result = compare_profiles(populated_base, "dev", "prod")
    assert "DEBUG" in result["only_in_a"]


def test_compare_only_in_b(populated_base):
    from env_vault.compare import compare_profiles
    result = compare_profiles(populated_base, "dev", "prod")
    assert "SECRET" in result["only_in_b"]


def test_compare_different_values(populated_base):
    from env_vault.compare import compare_profiles
    result = compare_profiles(populated_base, "dev", "prod")
    diff_keys = [e["key"] for e in result["in_both_different"]]
    assert "APP_ENV" in diff_keys


def test_compare_same_values(populated_base):
    from env_vault.compare import compare_profiles
    result = compare_profiles(populated_base, "dev", "prod")
    assert "SHARED" in result["in_both_same"]


def test_compare_show_values_includes_values(populated_base):
    from env_vault.compare import compare_profiles
    result = compare_profiles(populated_base, "dev", "prod", show_values=True)
    diff = {e["key"]: e for e in result["in_both_different"]}
    assert diff["APP_ENV"]["value_a"] == "development"
    assert diff["APP_ENV"]["value_b"] == "production"


def test_compare_missing_profile_raises(populated_base):
    from env_vault.compare import compare_profiles
    with pytest.raises(FileNotFoundError):
        compare_profiles(populated_base, "dev", "nonexistent")


def test_cli_compare_profiles_cmd(runner, populated_base):
    result = runner.invoke(
        compare_group,
        ["profiles", "dev", "prod", "--base-path", populated_base],
    )
    assert result.exit_code == 0
    assert "APP_ENV" in result.output


def test_cli_compare_show_values(runner, populated_base):
    result = runner.invoke(
        compare_group,
        ["profiles", "dev", "prod", "--show-values", "--base-path", populated_base],
    )
    assert result.exit_code == 0
    assert "development" in result.output
    assert "production" in result.output


def test_cli_compare_missing_vault(runner, populated_base):
    result = runner.invoke(
        compare_group,
        ["profiles", "dev", "ghost", "--base-path", populated_base],
    )
    assert result.exit_code != 0
    assert "Error" in result.output or "Error" in (result.output + str(result.exception))
