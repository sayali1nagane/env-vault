"""Tests for the CLI tags commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from env_vault.cli_tags import tags_group
from env_vault.storage import init_vault_dir
from env_vault.tags import add_tag


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_env(tmp_path: Path):
    """Initialised vault environment for CLI tests."""
    init_vault_dir(tmp_path, "default")
    return tmp_path


def test_add_cmd_shows_tag(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(tags_group, ["add", "production", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "production" in result.output


def test_add_cmd_empty_tag_fails(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(tags_group, ["add", "  ", "--base", str(vault_env)])
    assert result.exit_code != 0


def test_remove_cmd_succeeds(runner: CliRunner, vault_env: Path) -> None:
    add_tag(vault_env, "temp", "default")
    result = runner.invoke(tags_group, ["remove", "temp", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "temp" not in result.output


def test_remove_cmd_missing_tag_fails(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(tags_group, ["remove", "ghost", "--base", str(vault_env)])
    assert result.exit_code != 0


def test_list_cmd_no_tags(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(tags_group, ["list", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_list_cmd_shows_tags(runner: CliRunner, vault_env: Path) -> None:
    add_tag(vault_env, "ci", "default")
    add_tag(vault_env, "staging", "default")
    result = runner.invoke(tags_group, ["list", "--base", str(vault_env)])
    assert "ci" in result.output
    assert "staging" in result.output


def test_find_cmd_returns_matching_profiles(runner: CliRunner, vault_env: Path) -> None:
    init_vault_dir(vault_env, "prod")
    add_tag(vault_env, "cloud", "default")
    add_tag(vault_env, "cloud", "prod")
    result = runner.invoke(tags_group, ["find", "cloud", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "default" in result.output
    assert "prod" in result.output


def test_find_cmd_no_match(runner: CliRunner, vault_env: Path) -> None:
    result = runner.invoke(tags_group, ["find", "nope", "--base", str(vault_env)])
    assert result.exit_code == 0
    assert "No profiles" in result.output
