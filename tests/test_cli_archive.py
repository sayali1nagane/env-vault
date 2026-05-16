"""Tests for env_vault.cli_archive."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from env_vault.cli_archive import archive_group
from env_vault.crypto import generate_key
from env_vault.storage import init_vault_dir, write_vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path: Path):
    init_vault_dir(tmp_path, "default")
    write_vault(tmp_path, b"ciphertext", "default")
    return tmp_path


def _invoke(runner, vault_env, *args):
    return runner.invoke(archive_group, [*args, "--base", str(vault_env)])


def test_save_cmd_creates_archive(runner, vault_env):
    result = _invoke(runner, vault_env, "save", "default")
    assert result.exit_code == 0
    assert "Archived profile 'default'" in result.output


def test_save_cmd_with_custom_name(runner, vault_env):
    result = _invoke(runner, vault_env, "save", "default", "--name", "my-arc")
    assert result.exit_code == 0
    assert "my-arc" in result.output


def test_save_cmd_fails_for_missing_profile(runner, vault_env):
    result = _invoke(runner, vault_env, "save", "ghost")
    assert result.exit_code != 0
    assert "Error" in result.output


def test_list_cmd_empty(runner, vault_env):
    result = _invoke(runner, vault_env, "list")
    assert result.exit_code == 0
    assert "No archives found" in result.output


def test_list_cmd_shows_archive(runner, vault_env):
    _invoke(runner, vault_env, "save", "default", "--name", "listed-arc")
    result = _invoke(runner, vault_env, "list")
    assert result.exit_code == 0
    assert "listed-arc" in result.output


def test_restore_cmd_restores_profile(runner, vault_env):
    _invoke(runner, vault_env, "save", "default", "--name", "restore-test")
    result = _invoke(runner, vault_env, "restore", "restore-test")
    assert result.exit_code == 0
    assert "Restored profile" in result.output


def test_restore_cmd_fails_for_missing_archive(runner, vault_env):
    result = _invoke(runner, vault_env, "restore", "ghost-archive")
    assert result.exit_code != 0


def test_delete_cmd_removes_archive(runner, vault_env):
    _invoke(runner, vault_env, "save", "default", "--name", "del-arc")
    result = _invoke(runner, vault_env, "delete", "del-arc", "--yes")
    assert result.exit_code == 0
    assert "Deleted archive" in result.output


def test_delete_cmd_fails_for_missing_archive(runner, vault_env):
    result = _invoke(runner, vault_env, "delete", "no-such-arc", "--yes")
    assert result.exit_code != 0
    assert "Error" in result.output
