"""Tests for env_vault.cli_rotate CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from env_vault.crypto import generate_key, encrypt
from env_vault.storage import init_vault_dir, write_vault, save_key
from env_vault.cli_rotate import rotate_group

PROJECT = "clirotatetest"
PLAINTEXT = b"API_KEY=abc123\nSECRET=xyz\n"


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_env(tmp_path):
    key = generate_key()
    init_vault_dir(PROJECT, tmp_path)
    ciphertext = encrypt(PLAINTEXT, key)
    write_vault(PROJECT, tmp_path, ciphertext)
    save_key(PROJECT, tmp_path, key)
    return tmp_path


def test_rotate_cmd_succeeds(runner, vault_env):
    result = runner.invoke(
        rotate_group,
        ["run", PROJECT, "--base-path", str(vault_env)],
        input="y\n",
    )
    assert result.exit_code == 0
    assert "rotated successfully" in result.output


def test_rotate_cmd_aborted_on_no(runner, vault_env):
    result = runner.invoke(
        rotate_group,
        ["run", PROJECT, "--base-path", str(vault_env)],
        input="n\n",
    )
    assert result.exit_code != 0 or "Aborted" in result.output


def test_rotate_cmd_fails_for_missing_vault(runner, tmp_path):
    init_vault_dir(PROJECT, tmp_path)
    result = runner.invoke(
        rotate_group,
        ["run", PROJECT, "--base-path", str(tmp_path)],
        input="y\n",
    )
    assert result.exit_code != 0
    assert "Vault not found" in result.output or "Vault not found" in (result.output + str(result.exception))


def test_info_cmd_no_rotation(runner, vault_env):
    result = runner.invoke(
        rotate_group,
        ["info", PROJECT, "--base-path", str(vault_env)],
    )
    assert result.exit_code == 0
    assert "No rotation recorded" in result.output


def test_info_cmd_after_rotation(runner, vault_env):
    runner.invoke(
        rotate_group,
        ["run", PROJECT, "--base-path", str(vault_env)],
        input="y\n",
    )
    result = runner.invoke(
        rotate_group,
        ["info", PROJECT, "--base-path", str(vault_env)],
    )
    assert result.exit_code == 0
    assert "Last rotated:" in result.output
