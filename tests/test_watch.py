"""Tests for env_vault.watch and env_vault.cli_watch."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from env_vault.watch import (
    check_for_changes,
    clear_watch_state,
    load_watch_state,
    record_watch_state,
)
from env_vault.cli_watch import watch_group
from env_vault.storage import init_vault_dir


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    init_vault_dir(tmp_path)
    return tmp_path


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("KEY=value\nFOO=bar\n")
    return p


# --- unit tests ---

def test_record_watch_state_creates_file(tmp_base, env_file):
    state = record_watch_state(env_file, tmp_base)
    assert state["hash"] is not None
    assert state["mtime"] is not None
    assert load_watch_state(tmp_base) is not None


def test_load_watch_state_none_when_missing(tmp_base):
    assert load_watch_state(tmp_base) is None


def test_check_no_changes(tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    result = check_for_changes(env_file, tmp_base)
    assert result["changed"] is False
    assert result["reason"] is None


def test_check_detects_content_change(tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    env_file.write_text("KEY=newvalue\n")
    result = check_for_changes(env_file, tmp_base)
    assert result["changed"] is True
    assert result["reason"] == "content changed"


def test_check_detects_deletion(tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    env_file.unlink()
    result = check_for_changes(env_file, tmp_base)
    assert result["changed"] is True
    assert result["reason"] == "file deleted"


def test_check_no_previous_state(tmp_base, env_file):
    result = check_for_changes(env_file, tmp_base)
    assert result["changed"] is False
    assert "no previous state" in result["reason"]


def test_clear_watch_state(tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    clear_watch_state(tmp_base)
    assert load_watch_state(tmp_base) is None


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_base, env_file):
    return {"base_path": str(tmp_base), "env_file": str(env_file)}


def test_record_cmd(runner, vault_env):
    result = runner.invoke(
        watch_group, ["record", vault_env["env_file"]],
        obj={"base_path": vault_env["base_path"]}
    )
    assert result.exit_code == 0
    assert "Recorded state" in result.output


def test_check_cmd_no_change(runner, vault_env, tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    result = runner.invoke(
        watch_group, ["check", vault_env["env_file"]],
        obj={"base_path": vault_env["base_path"]}
    )
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_check_cmd_detects_change(runner, vault_env, tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    env_file.write_text("CHANGED=true\n")
    result = runner.invoke(
        watch_group, ["check", vault_env["env_file"]],
        obj={"base_path": vault_env["base_path"]}
    )
    assert result.exit_code == 1
    assert "CHANGED" in result.output


def test_clear_cmd(runner, vault_env, tmp_base, env_file):
    record_watch_state(env_file, tmp_base)
    result = runner.invoke(
        watch_group, ["clear"],
        obj={"base_path": vault_env["base_path"]}
    )
    assert result.exit_code == 0
    assert load_watch_state(tmp_base) is None
