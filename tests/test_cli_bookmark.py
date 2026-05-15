"""Tests for env_vault.cli_bookmark CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from env_vault.cli_bookmark import bookmark_group
from env_vault.bookmark import set_bookmark


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path):
    vault_dir = tmp_path / ".env-vault"
    vault_dir.mkdir()
    return {"ENV_VAULT_BASE": str(tmp_path)}


def test_add_cmd_creates_bookmark(runner, vault_env):
    result = runner.invoke(bookmark_group, ["add", "mydb", "DATABASE_URL", "prod"], env=vault_env)
    assert result.exit_code == 0
    assert "mydb" in result.output
    assert "prod:DATABASE_URL" in result.output


def test_add_cmd_with_note(runner, vault_env):
    result = runner.invoke(
        bookmark_group,
        ["add", "sec", "SECRET_KEY", "staging", "--note", "Django secret"],
        env=vault_env,
    )
    assert result.exit_code == 0
    assert "Django secret" in result.output


def test_list_cmd_empty(runner, vault_env):
    result = runner.invoke(bookmark_group, ["list"], env=vault_env)
    assert result.exit_code == 0
    assert "No bookmarks" in result.output


def test_list_cmd_shows_entries(runner, vault_env):
    set_bookmark(vault_env["ENV_VAULT_BASE"], "alpha", "ALPHA_KEY", "dev")
    result = runner.invoke(bookmark_group, ["list"], env=vault_env)
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "ALPHA_KEY" in result.output


def test_get_cmd_shows_details(runner, vault_env):
    set_bookmark(vault_env["ENV_VAULT_BASE"], "tok", "API_TOKEN", "prod", note="Main token")
    result = runner.invoke(bookmark_group, ["get", "tok"], env=vault_env)
    assert result.exit_code == 0
    assert "API_TOKEN" in result.output
    assert "prod" in result.output
    assert "Main token" in result.output


def test_get_cmd_fails_for_missing(runner, vault_env):
    result = runner.invoke(bookmark_group, ["get", "ghost"], env=vault_env)
    assert result.exit_code != 0


def test_remove_cmd_succeeds(runner, vault_env):
    set_bookmark(vault_env["ENV_VAULT_BASE"], "bye", "BYE_KEY", "dev")
    result = runner.invoke(bookmark_group, ["remove", "bye"], env=vault_env)
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_remove_cmd_fails_for_missing(runner, vault_env):
    result = runner.invoke(bookmark_group, ["remove", "nope"], env=vault_env)
    assert result.exit_code != 0


def test_find_cmd_returns_matches(runner, vault_env):
    base = vault_env["ENV_VAULT_BASE"]
    set_bookmark(base, "a", "DB_URL", "dev")
    set_bookmark(base, "b", "DB_URL", "prod")
    result = runner.invoke(bookmark_group, ["find", "DB_URL"], env=vault_env)
    assert result.exit_code == 0
    assert "a" in result.output
    assert "b" in result.output


def test_find_cmd_no_matches(runner, vault_env):
    result = runner.invoke(bookmark_group, ["find", "UNKNOWN_KEY"], env=vault_env)
    assert result.exit_code == 0
    assert "No bookmarks" in result.output
