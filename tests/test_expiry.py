"""Tests for env_vault.expiry module."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from env_vault.expiry import (
    set_expiry,
    remove_expiry,
    get_expiry,
    list_expiries,
    check_expired_keys,
)


@pytest.fixture()
def tmp_base(tmp_path: Path) -> str:
    # Ensure vault dir exists for default profile
    vault_dir = tmp_path / ".env-vault" / "default"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return str(tmp_path)


FUTURE = datetime.now(timezone.utc) + timedelta(days=30)
PAST = datetime.now(timezone.utc) - timedelta(days=1)


def test_get_expiry_none_when_missing(tmp_base):
    assert get_expiry("MISSING_KEY", tmp_base) is None


def test_set_and_get_expiry(tmp_base):
    set_expiry("API_KEY", FUTURE, tmp_base)
    result = get_expiry("API_KEY", tmp_base)
    assert result is not None
    assert abs((result - FUTURE).total_seconds()) < 1


def test_set_expiry_normalises_key_to_uppercase(tmp_base):
    set_expiry("api_key", FUTURE, tmp_base)
    assert get_expiry("API_KEY", tmp_base) is not None
    assert get_expiry("api_key", tmp_base) is not None


def test_set_expiry_stores_utc(tmp_base):
    set_expiry("TOKEN", FUTURE, tmp_base)
    result = get_expiry("TOKEN", tmp_base)
    assert result.tzinfo is not None
    assert result.tzinfo == timezone.utc


def test_remove_expiry_returns_true_when_exists(tmp_base):
    set_expiry("DB_PASS", FUTURE, tmp_base)
    assert remove_expiry("DB_PASS", tmp_base) is True
    assert get_expiry("DB_PASS", tmp_base) is None


def test_remove_expiry_returns_false_when_missing(tmp_base):
    assert remove_expiry("NO_SUCH_KEY", tmp_base) is False


def test_list_expiries_empty_by_default(tmp_base):
    assert list_expiries(tmp_base) == {}


def test_list_expiries_returns_all_keys(tmp_base):
    set_expiry("KEY_A", FUTURE, tmp_base)
    set_expiry("KEY_B", PAST, tmp_base)
    result = list_expiries(tmp_base)
    assert set(result.keys()) == {"KEY_A", "KEY_B"}


def test_check_expired_keys_empty_when_none_expired(tmp_base):
    set_expiry("FRESH_KEY", FUTURE, tmp_base)
    assert check_expired_keys(tmp_base) == []


def test_check_expired_keys_detects_past_expiry(tmp_base):
    set_expiry("OLD_TOKEN", PAST, tmp_base)
    expired = check_expired_keys(tmp_base)
    assert "OLD_TOKEN" in expired


def test_check_expired_keys_mixed(tmp_base):
    set_expiry("FRESH", FUTURE, tmp_base)
    set_expiry("STALE", PAST, tmp_base)
    expired = check_expired_keys(tmp_base)
    assert "STALE" in expired
    assert "FRESH" not in expired
