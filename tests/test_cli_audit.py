"""Tests for audit CLI commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from env_vault.cli_audit import audit_group
from env_vault.audit import append_audit_entry
from env_vault.storage import init_vault_dir


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_env(tmp_path):
    init_vault_dir(tmp_path)
    return tmp_path


def test_log_cmd_no_entries(runner, vault_env):
    result = runner.invoke(audit_group, ["log", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "No audit log" in result.output


def test_log_cmd_shows_entries(runner, vault_env):
    append_audit_entry(vault_env, "init")
    append_audit_entry(vault_env, "set", {"key": "SECRET"})
    result = runner.invoke(audit_group, ["log", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "set" in result.output
    assert "SECRET" in result.output


def test_log_cmd_filter_by_action(runner, vault_env):
    append_audit_entry(vault_env, "init")
    append_audit_entry(vault_env, "export", {"file": "out.zip"})
    result = runner.invoke(
        audit_group, ["log", "--base", str(vault_env), "--action", "export"]
    )
    assert result.exit_code == 0
    assert "export" in result.output
    assert "init" not in result.output


def test_log_cmd_filter_action_no_match(runner, vault_env):
    append_audit_entry(vault_env, "init")
    result = runner.invoke(
        audit_group, ["log", "--base", str(vault_env), "--action", "nonexistent"]
    )
    assert result.exit_code == 0
    assert "No entries found" in result.output


def test_log_cmd_last_n_entries(runner, vault_env):
    for i in range(5):
        append_audit_entry(vault_env, "set", {"key": f"VAR_{i}"})
    result = runner.invoke(
        audit_group, ["log", "--base", str(vault_env), "--last", "2"]
    )
    assert result.exit_code == 0
    assert "VAR_4" in result.output
    assert "VAR_3" in result.output
    assert "VAR_0" not in result.output


def test_clear_cmd_removes_log(runner, vault_env):
    append_audit_entry(vault_env, "init")
    result = runner.invoke(
        audit_group, ["clear", "--base", str(vault_env)], input="y\n"
    )
    assert result.exit_code == 0
    assert "cleared" in result.output
    from env_vault.audit import get_audit_path
    assert get_audit_path(vault_env).read_text() == ""


def test_clear_cmd_no_log_file(runner, vault_env):
    result = runner.invoke(
        audit_group, ["clear", "--base", str(vault_env)], input="y\n"
    )
    assert result.exit_code == 0
    assert "No audit log found" in result.output
