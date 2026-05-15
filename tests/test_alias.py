"""Tests for env_vault.alias."""

import pytest

from env_vault.alias import (
    list_aliases,
    set_alias,
    remove_alias,
    resolve_alias,
)


@pytest.fixture()
def tmp_base(tmp_path):
    base = str(tmp_path)
    # Ensure vault dir exists
    from env_vault.storage import init_vault_dir
    init_vault_dir(base)
    return base


def test_list_aliases_empty_by_default(tmp_base):
    assert list_aliases(tmp_base) == {}


def test_set_alias_creates_entry(tmp_base):
    set_alias(tmp_base, "prod", "production")
    aliases = list_aliases(tmp_base)
    assert aliases["prod"] == "production"


def test_set_alias_normalises_to_lowercase(tmp_base):
    set_alias(tmp_base, "PROD", "production")
    aliases = list_aliases(tmp_base)
    assert "prod" in aliases
    assert "PROD" not in aliases


def test_set_alias_overwrites_existing(tmp_base):
    set_alias(tmp_base, "p", "production")
    set_alias(tmp_base, "p", "preview")
    assert list_aliases(tmp_base)["p"] == "preview"


def test_set_alias_raises_if_same_as_profile(tmp_base):
    with pytest.raises(ValueError, match="differ"):
        set_alias(tmp_base, "production", "production")


def test_set_alias_raises_if_empty(tmp_base):
    with pytest.raises(ValueError, match="empty"):
        set_alias(tmp_base, "  ", "production")


def test_remove_alias_returns_true_when_found(tmp_base):
    set_alias(tmp_base, "prod", "production")
    assert remove_alias(tmp_base, "prod") is True
    assert "prod" not in list_aliases(tmp_base)


def test_remove_alias_returns_false_when_missing(tmp_base):
    assert remove_alias(tmp_base, "nonexistent") is False


def test_resolve_alias_returns_profile(tmp_base):
    set_alias(tmp_base, "prod", "production")
    assert resolve_alias(tmp_base, "prod") == "production"


def test_resolve_alias_returns_input_when_no_match(tmp_base):
    assert resolve_alias(tmp_base, "staging") == "staging"


def test_resolve_alias_is_case_insensitive(tmp_base):
    set_alias(tmp_base, "prod", "production")
    assert resolve_alias(tmp_base, "PROD") == "production"
