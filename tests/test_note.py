"""Tests for env_vault.note and env_vault.cli_note."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from env_vault.note import (
    clear_notes,
    get_note,
    list_notes,
    remove_note,
    set_note,
)
from env_vault.cli_note import note_group


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_base(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def runner(tmp_base):
    r = CliRunner()
    r.env = {"ENV_VAULT_BASE": tmp_base, "ENV_VAULT_PROFILE": "default"}
    return r, tmp_base


# ---------------------------------------------------------------------------
# Unit tests for note.py
# ---------------------------------------------------------------------------

def test_get_note_none_when_missing(tmp_base):
    assert get_note("API_KEY", tmp_base) is None


def test_set_and_get_note(tmp_base):
    set_note("API_KEY", "Production API key", tmp_base)
    assert get_note("API_KEY", tmp_base) == "Production API key"


def test_set_note_normalises_key_to_uppercase(tmp_base):
    set_note("db_pass", "database password", tmp_base)
    assert get_note("DB_PASS", tmp_base) == "database password"


def test_set_note_empty_string_removes_entry(tmp_base):
    set_note("TOKEN", "some note", tmp_base)
    set_note("TOKEN", "", tmp_base)
    assert get_note("TOKEN", tmp_base) is None


def test_remove_note_returns_true_when_existed(tmp_base):
    set_note("SECRET", "my secret", tmp_base)
    assert remove_note("SECRET", tmp_base) is True
    assert get_note("SECRET", tmp_base) is None


def test_remove_note_returns_false_when_missing(tmp_base):
    assert remove_note("NONEXISTENT", tmp_base) is False


def test_list_notes_empty_by_default(tmp_base):
    assert list_notes(tmp_base) == {}


def test_list_notes_returns_all_entries(tmp_base):
    set_note("A", "note a", tmp_base)
    set_note("B", "note b", tmp_base)
    notes = list_notes(tmp_base)
    assert notes == {"A": "note a", "B": "note b"}


def test_clear_notes_returns_count(tmp_base):
    set_note("X", "x", tmp_base)
    set_note("Y", "y", tmp_base)
    assert clear_notes(tmp_base) == 2
    assert list_notes(tmp_base) == {}


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

def test_cli_set_and_get(runner):
    r, base = runner
    result = r.invoke(note_group, ["set", "MY_KEY", "hello world"], env={"ENV_VAULT_BASE": base})
    assert result.exit_code == 0
    assert "MY_KEY" in result.output

    result = r.invoke(note_group, ["get", "MY_KEY"], env={"ENV_VAULT_BASE": base})
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_cli_list_empty(runner):
    r, base = runner
    result = r.invoke(note_group, ["list"], env={"ENV_VAULT_BASE": base})
    assert result.exit_code == 0
    assert "No notes" in result.output


def test_cli_remove_existing(runner):
    r, base = runner
    r.invoke(note_group, ["set", "K", "v"], env={"ENV_VAULT_BASE": base})
    result = r.invoke(note_group, ["remove", "K"], env={"ENV_VAULT_BASE": base})
    assert result.exit_code == 0
    assert "removed" in result.output
