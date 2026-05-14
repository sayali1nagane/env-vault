"""Tests for env_vault.cli_history CLI commands."""

from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

from env_vault.cli_history import history_group
from env_vault.history import record_change
from env_vault.storage import init_vault_dir


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path: Path):
    init_vault_dir(tmp_path, "default")
    return {"base_path": str(tmp_path)}


def test_log_cmd_no_history(runner: CliRunner, vault_env: dict) -> None:
    result = runner.invoke(history_group, ["log", "API_KEY"], obj=vault_env)
    assert result.exit_code == 0
    assert "No history" in result.output


def test_log_cmd_shows_entries(runner: CliRunner, vault_env: dict, tmp_path: Path) -> None:
    record_change(tmp_path, "API_KEY", None, "secret123", actor="cli")
    result = runner.invoke(history_group, ["log", "API_KEY"], obj=vault_env)
    assert result.exit_code == 0
    assert "secret123" in result.output
    assert "(unset)" in result.output


def test_keys_cmd_empty(runner: CliRunner, vault_env: dict) -> None:
    result = runner.invoke(history_group, ["keys"], obj=vault_env)
    assert result.exit_code == 0
    assert "No history" in result.output


def test_keys_cmd_lists_tracked(runner: CliRunner, vault_env: dict, tmp_path: Path) -> None:
    record_change(tmp_path, "DB_URL", None, "postgres://localhost/db")
    result = runner.invoke(history_group, ["keys"], obj=vault_env)
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_clear_cmd_with_yes_flag(runner: CliRunner, vault_env: dict, tmp_path: Path) -> None:
    record_change(tmp_path, "TOKEN", None, "abc")
    result = runner.invoke(history_group, ["clear", "TOKEN", "--yes"], obj=vault_env)
    assert result.exit_code == 0
    assert "cleared" in result.output


def test_clear_cmd_aborted_on_no(runner: CliRunner, vault_env: dict, tmp_path: Path) -> None:
    record_change(tmp_path, "TOKEN", None, "abc")
    result = runner.invoke(history_group, ["clear", "TOKEN"], input="n\n", obj=vault_env)
    assert result.exit_code != 0
