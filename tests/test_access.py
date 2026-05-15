"""Tests for env_vault.access."""

from __future__ import annotations

import pytest

from env_vault.access import (
    _access_path,
    can,
    get_permissions,
    list_actors,
    revoke_permissions,
    set_permissions,
)


@pytest.fixture()
def tmp_base(tmp_path):
    return str(tmp_path)


def test_get_permissions_defaults_to_full_access(tmp_base):
    perms = get_permissions(tmp_base, "default", "alice")
    assert "read" in perms
    assert "write" in perms


def test_set_permissions_persists(tmp_base):
    set_permissions(tmp_base, "default", "alice", ["read"])
    perms = get_permissions(tmp_base, "default", "alice")
    assert perms == ["read"]


def test_set_permissions_rejects_unknown(tmp_base):
    with pytest.raises(ValueError, match="Unknown permissions"):
        set_permissions(tmp_base, "default", "alice", ["execute"])


def test_set_permissions_deduplicates(tmp_base):
    set_permissions(tmp_base, "default", "bob", ["read", "read", "write"])
    perms = get_permissions(tmp_base, "default", "bob")
    assert perms.count("read") == 1


def test_can_returns_true_when_permitted(tmp_base):
    set_permissions(tmp_base, "default", "carol", ["read", "write"])
    assert can(tmp_base, "default", "carol", "read") is True
    assert can(tmp_base, "default", "carol", "write") is True


def test_can_returns_false_when_not_permitted(tmp_base):
    set_permissions(tmp_base, "default", "dave", ["read"])
    assert can(tmp_base, "default", "dave", "write") is False


def test_revoke_removes_entry(tmp_base):
    set_permissions(tmp_base, "default", "eve", ["read"])
    removed = revoke_permissions(tmp_base, "default", "eve")
    assert removed is True
    # After revoke, defaults (full access) apply
    assert can(tmp_base, "default", "eve", "write") is True


def test_revoke_returns_false_when_no_entry(tmp_base):
    removed = revoke_permissions(tmp_base, "default", "nobody")
    assert removed is False


def test_list_actors_empty_by_default(tmp_base):
    actors = list_actors(tmp_base, "default")
    assert actors == {}


def test_list_actors_returns_all(tmp_base):
    set_permissions(tmp_base, "staging", "alice", ["read"])
    set_permissions(tmp_base, "staging", "bob", ["read", "write"])
    actors = list_actors(tmp_base, "staging")
    assert set(actors.keys()) == {"alice", "bob"}


def test_access_path_is_inside_vault_dir(tmp_base):
    path = _access_path(tmp_base, "production")
    assert "production" in str(path)
    assert path.name == "access.json"
