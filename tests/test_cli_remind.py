"""Tests for env_vault.cli_remind."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

from env_vault.cli_remind import remind_group
from env_vault.storage import get_vault_dir


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path: Path):
    get_vault_dir(tmp_path).mkdir(parents=True, exist_ok=True)
    return tmp_path


def _write_meta(base: Path, profile: str, days_ago: int) -> None:
    vault_dir = get_vault_dir(base) / profile
    vault_dir.mkdir(parents=True, exist_ok=True)
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    (vault_dir / "meta.json").write_text(json.dumps({"last_rotated": ts}))


def test_status_cmd_not_due(runner: CliRunner, vault_env: Path) -> None:
    from env_vault.remind import set_reminder_config
    set_reminder_config(vault_env, interval_days=30)
    _write_meta(vault_env, "default", days_ago=5)
    result = runner.invoke(remind_group, ["status", "--base-path", str(vault_env)])
    assert result.exit_code == 0
    assert "not due" in result.output


def test_status_cmd_overdue(runner: CliRunner, vault_env: Path) -> None:
    from env_vault.remind import set_reminder_config
    set_reminder_config(vault_env, interval_days=10)
    _write_meta(vault_env, "default", days_ago=20)
    result = runner.invoke(remind_group, ["status", "--base-path", str(vault_env)])
    assert result.exit_code == 0
    assert "OVERDUE" in result.output


def test_status_cmd_disabled(runner: CliRunner, vault_env: Path) -> None:
    from env_vault.remind import set_reminder_config
    set_reminder_config(vault_env, interval_days=1, enabled=False)
    _write_meta(vault_env, "default", days_ago=999)
    result = runner.invoke(remind_group, ["status", "--base-path", str(vault_env)])
    assert result.exit_code == 0
    assert "disabled" in result.output


def test_configure_cmd_sets_interval(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(
        remind_group, ["configure", "--base-path", str(vault_env), "--interval", "14"]
    )
    assert result.exit_code == 0
    assert "14" in result.output
    from env_vault.remind import get_reminder_config
    assert get_reminder_config(vault_env)["interval_days"] == 14


def test_configure_cmd_disable_flag(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(
        remind_group,
        ["configure", "--base-path", str(vault_env), "--interval", "7", "--disable"],
    )
    assert result.exit_code == 0
    assert "disabled" in result.output


def test_configure_cmd_invalid_interval(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(
        remind_group, ["configure", "--base-path", str(vault_env), "--interval", "0"]
    )
    assert result.exit_code != 0
