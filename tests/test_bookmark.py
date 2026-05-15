"""Tests for env_vault.bookmark."""

from __future__ import annotations

import pytest
from pathlib import Path
from env_vault.bookmark import (
    list_bookmarks,
    set_bookmark,
    get_bookmark,
    remove_bookmark,
    find_bookmarks_for_key,
)


@pytest.fixture()
def tmp_base(tmp_path: Path) -> str:
    vault_dir = tmp_path / ".env-vault"
    vault_dir.mkdir()
    return str(tmp_path)


def test_list_bookmarks_empty_by_default(tmp_base):
    assert list_bookmarks(tmp_base) == {}


def test_set_bookmark_creates_entry(tmp_base):
    entry = set_bookmark(tmp_base, "mydb", "DATABASE_URL", "production")
    assert entry["key"] == "DATABASE_URL"
    assert entry["profile"] == "production"
    assert entry["note"] == ""


def test_set_bookmark_normalises_name_to_lowercase(tmp_base):
    set_bookmark(tmp_base, "MyDB", "DATABASE_URL", "staging")
    assert "mydb" in list_bookmarks(tmp_base)


def test_set_bookmark_normalises_key_to_uppercase(tmp_base):
    entry = set_bookmark(tmp_base, "tok", "api_token", "dev")
    assert entry["key"] == "API_TOKEN"


def test_set_bookmark_stores_note(tmp_base):
    entry = set_bookmark(tmp_base, "main", "SECRET_KEY", "default", note="Django secret")
    assert entry["note"] == "Django secret"


def test_set_bookmark_overwrites_existing(tmp_base):
    set_bookmark(tmp_base, "tok", "OLD_KEY", "dev")
    set_bookmark(tmp_base, "tok", "NEW_KEY", "prod")
    entry = get_bookmark(tmp_base, "tok")
    assert entry["key"] == "NEW_KEY"
    assert entry["profile"] == "prod"


def test_get_bookmark_returns_none_when_missing(tmp_base):
    assert get_bookmark(tmp_base, "ghost") is None


def test_get_bookmark_returns_entry(tmp_base):
    set_bookmark(tmp_base, "db", "DB_URL", "prod", note="main db")
    entry = get_bookmark(tmp_base, "db")
    assert entry is not None
    assert entry["key"] == "DB_URL"


def test_remove_bookmark_returns_true_when_exists(tmp_base):
    set_bookmark(tmp_base, "x", "X_KEY", "dev")
    assert remove_bookmark(tmp_base, "x") is True


def test_remove_bookmark_returns_false_when_missing(tmp_base):
    assert remove_bookmark(tmp_base, "nope") is False


def test_remove_bookmark_deletes_entry(tmp_base):
    set_bookmark(tmp_base, "y", "Y_KEY", "dev")
    remove_bookmark(tmp_base, "y")
    assert get_bookmark(tmp_base, "y") is None


def test_find_bookmarks_for_key_returns_matches(tmp_base):
    set_bookmark(tmp_base, "a", "DB_URL", "dev")
    set_bookmark(tmp_base, "b", "DB_URL", "prod")
    set_bookmark(tmp_base, "c", "OTHER_KEY", "dev")
    results = find_bookmarks_for_key(tmp_base, "DB_URL")
    names = {r["name"] for r in results}
    assert names == {"a", "b"}


def test_find_bookmarks_case_insensitive_key(tmp_base):
    set_bookmark(tmp_base, "tok", "API_TOKEN", "dev")
    results = find_bookmarks_for_key(tmp_base, "api_token")
    assert len(results) == 1


def test_set_bookmark_raises_on_empty_name(tmp_base):
    with pytest.raises(ValueError):
        set_bookmark(tmp_base, "", "KEY", "dev")
