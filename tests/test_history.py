"""Tests for env_vault.history."""

from __future__ import annotations

import pytest
from pathlib import Path

from env_vault.history import (
    clear_key_history,
    get_history_path,
    get_key_history,
    list_tracked_keys,
    record_change,
)
from env_vault.storage import init_vault_dir


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    init_vault_dir(tmp_path, "default")
    return tmp_path


def test_get_history_path_is_inside_vault(tmp_base: Path) -> None:
    path = get_history_path(tmp_base, "default")
    assert path.parent.name == "default"
    assert path.name == "history.json"


def test_get_key_history_empty_when_no_file(tmp_base: Path) -> None:
    assert get_key_history(tmp_base, "API_KEY") == []


def test_record_change_creates_entry(tmp_base: Path) -> None:
    record_change(tmp_base, "API_KEY", None, "abc123")
    entries = get_key_history(tmp_base, "API_KEY")
    assert len(entries) == 1
    assert entries[0]["new"] == "abc123"
    assert entries[0]["old"] is None


def test_record_change_appends_multiple(tmp_base: Path) -> None:
    record_change(tmp_base, "TOKEN", None, "v1")
    record_change(tmp_base, "TOKEN", "v1", "v2")
    entries = get_key_history(tmp_base, "TOKEN")
    assert len(entries) == 2
    assert entries[-1]["new"] == "v2"


def test_record_change_stores_actor(tmp_base: Path) -> None:
    record_change(tmp_base, "DB_PASS", None, "secret", actor="test-suite")
    entry = get_key_history(tmp_base, "DB_PASS")[0]
    assert entry["actor"] == "test-suite"


def test_list_tracked_keys_empty(tmp_base: Path) -> None:
    assert list_tracked_keys(tmp_base) == []


def test_list_tracked_keys_returns_sorted(tmp_base: Path) -> None:
    record_change(tmp_base, "Z_KEY", None, "1")
    record_change(tmp_base, "A_KEY", None, "2")
    assert list_tracked_keys(tmp_base) == ["A_KEY", "Z_KEY"]


def test_clear_key_history_removes_entries(tmp_base: Path) -> None:
    record_change(tmp_base, "API_KEY", None, "val")
    clear_key_history(tmp_base, "API_KEY")
    assert get_key_history(tmp_base, "API_KEY") == []


def test_clear_key_history_noop_if_missing(tmp_base: Path) -> None:
    # Should not raise even if key never existed
    clear_key_history(tmp_base, "NONEXISTENT")


def test_history_isolated_by_profile(tmp_base: Path) -> None:
    init_vault_dir(tmp_base, "staging")
    record_change(tmp_base, "KEY", None, "prod-val", profile="default")
    record_change(tmp_base, "KEY", None, "stg-val", profile="staging")
    assert get_key_history(tmp_base, "KEY", "default")[0]["new"] == "prod-val"
    assert get_key_history(tmp_base, "KEY", "staging")[0]["new"] == "stg-val"
