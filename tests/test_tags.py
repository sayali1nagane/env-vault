"""Tests for env_vault.tags module."""

from __future__ import annotations

import pytest
from pathlib import Path

from env_vault.storage import init_vault_dir, save_meta, load_meta
from env_vault.tags import add_tag, get_tags, list_profiles_by_tag, remove_tag


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    """Base path with a default vault initialised."""
    init_vault_dir(tmp_path, "default")
    return tmp_path


def test_get_tags_empty_by_default(tmp_base: Path) -> None:
    assert get_tags(tmp_base, "default") == []


def test_add_tag_returns_list(tmp_base: Path) -> None:
    result = add_tag(tmp_base, "production", "default")
    assert "production" in result


def test_add_tag_normalises_to_lowercase(tmp_base: Path) -> None:
    add_tag(tmp_base, "Staging", "default")
    assert "staging" in get_tags(tmp_base, "default")


def test_add_tag_no_duplicates(tmp_base: Path) -> None:
    add_tag(tmp_base, "ci", "default")
    add_tag(tmp_base, "ci", "default")
    assert get_tags(tmp_base, "default").count("ci") == 1


def test_add_empty_tag_raises(tmp_base: Path) -> None:
    with pytest.raises(ValueError):
        add_tag(tmp_base, "  ", "default")


def test_remove_tag_succeeds(tmp_base: Path) -> None:
    add_tag(tmp_base, "dev", "default")
    remaining = remove_tag(tmp_base, "dev", "default")
    assert "dev" not in remaining


def test_remove_nonexistent_tag_raises(tmp_base: Path) -> None:
    with pytest.raises(KeyError):
        remove_tag(tmp_base, "ghost", "default")


def test_tags_persisted_in_meta(tmp_base: Path) -> None:
    add_tag(tmp_base, "infra", "default")
    meta = load_meta(tmp_base, "default")
    assert "infra" in meta["tags"]


def test_list_profiles_by_tag(tmp_base: Path) -> None:
    init_vault_dir(tmp_base, "staging")
    init_vault_dir(tmp_base, "prod")
    add_tag(tmp_base, "cloud", "staging")
    add_tag(tmp_base, "cloud", "prod")
    add_tag(tmp_base, "local", "default")
    result = list_profiles_by_tag(tmp_base, "cloud")
    assert "staging" in result
    assert "prod" in result
    assert "default" not in result


def test_list_profiles_by_tag_empty_when_none_match(tmp_base: Path) -> None:
    result = list_profiles_by_tag(tmp_base, "nonexistent")
    assert result == []


def test_list_profiles_by_tag_no_vault_dir(tmp_path: Path) -> None:
    result = list_profiles_by_tag(tmp_path, "anything")
    assert result == []
