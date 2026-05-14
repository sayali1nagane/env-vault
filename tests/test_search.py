"""Tests for env_vault.search."""

from __future__ import annotations

import pytest

from env_vault.crypto import generate_key, save_key, encrypt
from env_vault.storage import init_vault_dir, write_vault
from env_vault.search import search_keys, find_key_in_profiles


@pytest.fixture()
def populated_base(tmp_path):
    """Create two profiles with known env content."""
    profiles = {
        "default": "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n",
        "staging": "DB_HOST=staging.example.com\nAPI_KEY=xyz789\n",
    }
    for prof, content in profiles.items():
        init_vault_dir(str(tmp_path), prof)
        key = generate_key()
        save_key(str(tmp_path), key, prof)
        ciphertext = encrypt(content, key)
        write_vault(str(tmp_path), ciphertext, prof)
    return str(tmp_path)


def test_search_keys_finds_match_in_single_profile(populated_base):
    results = search_keys("DB_", base_path=populated_base, profile="default")
    assert "default" in results
    assert "DB_HOST" in results["default"]
    assert "DB_PORT" in results["default"]
    assert "SECRET_KEY" not in results["default"]


def test_search_keys_case_insensitive(populated_base):
    results = search_keys("db_host", base_path=populated_base)
    all_keys = {k for matches in results.values() for k in matches}
    assert "DB_HOST" in all_keys


def test_search_keys_across_all_profiles(populated_base):
    results = search_keys("DB_HOST", base_path=populated_base)
    assert "default" in results
    assert "staging" in results


def test_search_keys_only_hides_values(populated_base):
    results = search_keys("DB_HOST", base_path=populated_base, keys_only=True)
    for matches in results.values():
        for value in matches.values():
            assert value == "***"


def test_search_keys_no_match_returns_empty(populated_base):
    results = search_keys("NONEXISTENT_KEY_XYZ", base_path=populated_base)
    assert results == {}


def test_search_keys_missing_vault_skipped(populated_base):
    # Searching a profile that doesn't exist should not raise
    results = search_keys("DB", base_path=populated_base, profile="ghost")
    assert results == {}


def test_find_key_in_profiles_returns_correct_profiles(populated_base):
    profiles = find_key_in_profiles("DB_HOST", base_path=populated_base)
    assert "default" in profiles
    assert "staging" in profiles


def test_find_key_in_profiles_partial_name_not_matched(populated_base):
    # find_key_in_profiles uses exact key match, not substring
    profiles = find_key_in_profiles("DB", base_path=populated_base)
    assert profiles == []


def test_find_key_in_profiles_unique_key(populated_base):
    profiles = find_key_in_profiles("SECRET_KEY", base_path=populated_base)
    assert profiles == ["default"]


def test_find_key_in_profiles_empty_vault(tmp_path):
    profiles = find_key_in_profiles("ANY_KEY", base_path=str(tmp_path))
    assert profiles == []
