"""Tests for env_vault.sync and env_vault.cli_sync."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from env_vault.crypto import generate_key, save_key, encrypt
from env_vault.parser import serialize_env_dict
from env_vault.storage import init_vault_dir, write_vault
from env_vault.sync import diff_against_file, sync_from_file
from env_vault.cli_sync import sync_group


@pytest.fixture()
def vault_base(tmp_path: Path):
    base = tmp_path / ".vault"
    init_vault_dir(base, "default")
    key = generate_key()
    save_key(base, "default", key)
    env_data = {"FOO": "bar", "BAZ": "qux"}
    plaintext = serialize_env_dict(env_data).encode()
    write_vault(base, "default", encrypt(key, plaintext))
    return base


@pytest.fixture()
def env_file(tmp_path: Path):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    return f


def test_diff_no_changes(vault_base, env_file):
    result = diff_against_file(env_file, vault_base)
    assert not result.has_changes


def test_diff_detects_added_key(vault_base, env_file):
    env_file.write_text("FOO=bar\nBAZ=qux\nNEW=value\n")
    result = diff_against_file(env_file, vault_base)
    assert "NEW" in result.added
    assert not result.removed
    assert not result.updated


def test_diff_detects_removed_key(vault_base, env_file):
    env_file.write_text("FOO=bar\n")
    result = diff_against_file(env_file, vault_base)
    assert "BAZ" in result.removed


def test_diff_detects_updated_key(vault_base, env_file):
    env_file.write_text("FOO=changed\nBAZ=qux\n")
    result = diff_against_file(env_file, vault_base)
    assert "FOO" in result.updated


def test_sync_from_file_applies_changes(vault_base, env_file):
    env_file.write_text("FOO=newval\nEXTRA=yes\n")
    result = sync_from_file(env_file, vault_base)
    assert result.has_changes
    # verify vault now reflects new content
    result2 = diff_against_file(env_file, vault_base)
    assert not result2.has_changes


def test_diff_no_vault_reports_all_as_added(tmp_path, env_file):
    base = tmp_path / ".vault"
    base.mkdir()
    env_file.write_text("A=1\nB=2\n")
    result = diff_against_file(env_file, base)
    assert set(result.added) == {"A", "B"}


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_diff_no_changes(runner, vault_base, env_file):
    r = runner.invoke(sync_group, ["diff", str(env_file), "--base", str(vault_base)])
    assert r.exit_code == 0
    assert "up-to-date" in r.output


def test_cli_diff_shows_changes(runner, vault_base, env_file):
    env_file.write_text("FOO=changed\n")
    r = runner.invoke(sync_group, ["diff", str(env_file), "--base", str(vault_base)])
    assert r.exit_code == 0
    assert "~" in r.output or "-" in r.output


def test_cli_apply_with_yes_flag(runner, vault_base, env_file):
    env_file.write_text("FOO=updated\nBAZ=qux\n")
    r = runner.invoke(sync_group, ["apply", str(env_file), "--base", str(vault_base), "--yes"])
    assert r.exit_code == 0
    assert "updated" in r.output.lower()


def test_cli_apply_nothing_to_sync(runner, vault_base, env_file):
    r = runner.invoke(sync_group, ["apply", str(env_file), "--base", str(vault_base), "--yes"])
    assert r.exit_code == 0
    assert "Nothing to sync" in r.output
