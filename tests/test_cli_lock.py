"""Tests for env_vault.cli_lock CLI commands."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from click.testing import CliRunner

from env_vault.cli_lock import lock_group
from env_vault.lock import _lock_path, acquire_lock, release_lock


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path: Path):
    vault_dir = tmp_path / ".env-vault"
    vault_dir.mkdir()
    env = {"VAULT_BASE": str(tmp_path)}
    return tmp_path, env


def test_status_cmd_unlocked(runner: CliRunner, vault_env) -> None:
    base, env = vault_env
    result = runner.invoke(lock_group, ["status", "--base", str(base)], env=env)
    assert result.exit_code == 0
    assert "unlocked" in result.output.lower()


def test_status_cmd_locked(runner: CliRunner, vault_env) -> None:
    base, env = vault_env
    acquire_lock(base)
    result = runner.invoke(lock_group, ["status", "--base", str(base)], env=env)
    assert result.exit_code == 0
    assert "LOCKED" in result.output
    release_lock(base)


def test_acquire_cmd_creates_lock(runner: CliRunner, vault_env) -> None:
    base, env = vault_env
    result = runner.invoke(lock_group, ["acquire", "--base", str(base)], env=env)
    assert result.exit_code == 0
    assert "acquired" in result.output.lower()
    assert _lock_path(base).exists()
    release_lock(base)


def test_acquire_cmd_fails_on_timeout(runner: CliRunner, vault_env) -> None:
    base, env = vault_env
    lp = _lock_path(base)
    lp.write_text(json.dumps({"pid": 99999, "ts": time.time()}))
    result = runner.invoke(
        lock_group, ["acquire", "--base", str(base), "--timeout", "0"], env=env
    )
    assert result.exit_code != 0
    lp.unlink()


def test_release_cmd_removes_lock(runner: CliRunner, vault_env) -> None:
    base, env = vault_env
    acquire_lock(base)
    result = runner.invoke(lock_group, ["release", "--base", str(base)], env=env)
    assert result.exit_code == 0
    assert "released" in result.output.lower()
    assert not _lock_path(base).exists()


def test_release_cmd_when_not_locked(runner: CliRunner, vault_env) -> None:
    base, env = vault_env
    result = runner.invoke(lock_group, ["release", "--base", str(base)], env=env)
    assert result.exit_code == 0
    assert "nothing to release" in result.output.lower()
