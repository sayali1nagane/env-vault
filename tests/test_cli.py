"""Tests for the env-vault CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from env_vault.cli import cli
from env_vault.crypto import generate_key, save_key, encrypt
from env_vault.storage import init_vault_dir, write_vault, write_meta


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_env(tmp_path):
    """Set up a pre-initialized vault environment."""
    init_vault_dir(tmp_path)
    key = generate_key()
    save_key(key, tmp_path)
    write_meta({"version": 1, "entries": []}, tmp_path)
    return tmp_path, key


def test_init_creates_vault(runner, tmp_path):
    result = runner.invoke(cli, ["init", "--base", str(tmp_path)])
    assert result.exit_code == 0
    assert "Vault initialized" in result.output
    assert (tmp_path / ".env-vault").exists()
    assert (tmp_path / ".env-vault" / "key").exists()


def test_init_fails_if_already_initialized(runner, tmp_path):
    runner.invoke(cli, ["init", "--base", str(tmp_path)])
    result = runner.invoke(cli, ["init", "--base", str(tmp_path)])
    assert result.exit_code == 1
    assert "already initialized" in result.output


def test_set_encrypts_env_file(runner, vault_env, tmp_path):
    base_path, _ = vault_env
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=secret\nDEBUG=true\n")

    result = runner.invoke(cli, ["set", str(env_file), "--base", str(base_path)])
    assert result.exit_code == 0
    assert "Encrypted" in result.output
    assert (base_path / ".env-vault" / "vault.enc").exists()


def test_set_fails_if_file_missing(runner, vault_env, tmp_path):
    base_path, _ = vault_env
    result = runner.invoke(cli, ["set", str(tmp_path / "nonexistent.env"), "--base", str(base_path)])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_get_decrypts_to_file(runner, vault_env, tmp_path):
    base_path, key = vault_env
    original = "API_KEY=secret\nDEBUG=true\n"
    ciphertext = encrypt(key, original.encode())
    write_vault(ciphertext, base_path)

    output_file = tmp_path / "restored.env"
    result = runner.invoke(cli, ["get", str(output_file), "--base", str(base_path)])
    assert result.exit_code == 0
    assert "Decrypted" in result.output
    assert output_file.read_text() == original


def test_diff_shows_changes(runner, vault_env, tmp_path):
    base_path, key = vault_env
    vault_content = "API_KEY=old_secret\nDEBUG=false\n"
    ciphertext = encrypt(key, vault_content.encode())
    write_vault(ciphertext, base_path)

    local_env = tmp_path / ".env"
    local_env.write_text("API_KEY=new_secret\nNEW_VAR=hello\n")

    result = runner.invoke(cli, ["diff", str(local_env), "--base", str(base_path)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "NEW_VAR" in result.output


def test_diff_no_changes(runner, vault_env, tmp_path):
    base_path, key = vault_env
    content = "API_KEY=secret\n"
    ciphertext = encrypt(key, content.encode())
    write_vault(ciphertext, base_path)

    local_env = tmp_path / ".env"
    local_env.write_text(content)

    result = runner.invoke(cli, ["diff", str(local_env), "--base", str(base_path)])
    assert result.exit_code == 0
    assert "No changes" in result.output
