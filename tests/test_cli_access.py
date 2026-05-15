"""Tests for env_vault.cli_access."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from env_vault.cli_access import access_group


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path):
    return {"base_path": str(tmp_path)}


def _invoke(runner, vault_env, *args):
    return runner.invoke(access_group, list(args), obj=vault_env, catch_exceptions=False)


def test_grant_cmd_full_access(runner, vault_env):
    result = _invoke(runner, vault_env, "grant", "default", "alice")
    assert result.exit_code == 0
    assert "read" in result.output
    assert "write" in result.output


def test_grant_cmd_read_only(runner, vault_env):
    result = _invoke(runner, vault_env, "grant", "default", "bob", "--read", "--no-write")
    assert result.exit_code == 0
    assert "read" in result.output
    assert "write" not in result.output


def test_grant_cmd_fails_when_no_perms(runner, vault_env):
    result = runner.invoke(
        access_group,
        ["grant", "default", "carol", "--no-read", "--no-write"],
        obj=vault_env,
    )
    assert result.exit_code != 0


def test_revoke_cmd_existing_actor(runner, vault_env):
    _invoke(runner, vault_env, "grant", "default", "dave", "--read", "--no-write")
    result = _invoke(runner, vault_env, "revoke", "default", "dave")
    assert result.exit_code == 0
    assert "Revoked" in result.output


def test_revoke_cmd_unknown_actor(runner, vault_env):
    result = _invoke(runner, vault_env, "revoke", "default", "nobody")
    assert result.exit_code == 0
    assert "No explicit" in result.output


def test_show_cmd_empty(runner, vault_env):
    result = _invoke(runner, vault_env, "show", "default")
    assert result.exit_code == 0
    assert "No explicit" in result.output


def test_show_cmd_lists_actors(runner, vault_env):
    _invoke(runner, vault_env, "grant", "staging", "alice")
    _invoke(runner, vault_env, "grant", "staging", "bob", "--read", "--no-write")
    result = _invoke(runner, vault_env, "show", "staging")
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" in result.output


def test_check_cmd_allowed(runner, vault_env):
    _invoke(runner, vault_env, "grant", "default", "eve")
    result = _invoke(runner, vault_env, "check", "default", "eve", "write")
    assert result.exit_code == 0
    assert "allowed" in result.output


def test_check_cmd_denied(runner, vault_env):
    _invoke(runner, vault_env, "grant", "default", "frank", "--read", "--no-write")
    result = runner.invoke(
        access_group,
        ["check", "default", "frank", "write"],
        obj=vault_env,
        catch_exceptions=False,
    )
    assert result.exit_code == 1
    assert "denied" in result.output
