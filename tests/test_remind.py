"""Tests for env_vault.remind."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from env_vault.remind import (
    _DEFAULT_INTERVAL_DAYS,
    check_rotation_due,
    get_reminder_config,
    set_reminder_config,
)
from env_vault.storage import get_vault_dir


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path


def _write_meta(base: Path, profile: str, days_ago: int) -> None:
    vault_dir = get_vault_dir(base) / profile
    vault_dir.mkdir(parents=True, exist_ok=True)
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    (vault_dir / "meta.json").write_text(json.dumps({"last_rotated": ts}))


def test_get_reminder_config_defaults(tmp_base: Path) -> None:
    config = get_reminder_config(tmp_base)
    assert config["interval_days"] == _DEFAULT_INTERVAL_DAYS
    assert config["enabled"] is True


def test_set_reminder_config_persists(tmp_base: Path) -> None:
    get_vault_dir(tmp_base).mkdir(parents=True, exist_ok=True)
    config = set_reminder_config(tmp_base, interval_days=14)
    assert config["interval_days"] == 14
    assert config["enabled"] is True
    reloaded = get_reminder_config(tmp_base)
    assert reloaded["interval_days"] == 14


def test_set_reminder_config_can_disable(tmp_base: Path) -> None:
    get_vault_dir(tmp_base).mkdir(parents=True, exist_ok=True)
    config = set_reminder_config(tmp_base, interval_days=7, enabled=False)
    assert config["enabled"] is False


def test_set_reminder_config_rejects_zero(tmp_base: Path) -> None:
    with pytest.raises(ValueError):
        set_reminder_config(tmp_base, interval_days=0)


def test_check_rotation_not_due(tmp_base: Path) -> None:
    get_vault_dir(tmp_base).mkdir(parents=True, exist_ok=True)
    set_reminder_config(tmp_base, interval_days=30)
    _write_meta(tmp_base, "default", days_ago=10)
    assert check_rotation_due(tmp_base) is None


def test_check_rotation_overdue(tmp_base: Path) -> None:
    get_vault_dir(tmp_base).mkdir(parents=True, exist_ok=True)
    set_reminder_config(tmp_base, interval_days=30)
    _write_meta(tmp_base, "default", days_ago=45)
    overdue = check_rotation_due(tmp_base)
    assert overdue == 15


def test_check_rotation_disabled_returns_none(tmp_base: Path) -> None:
    get_vault_dir(tmp_base).mkdir(parents=True, exist_ok=True)
    set_reminder_config(tmp_base, interval_days=1, enabled=False)
    _write_meta(tmp_base, "default", days_ago=999)
    assert check_rotation_due(tmp_base) is None


def test_check_rotation_missing_meta_returns_none(tmp_base: Path) -> None:
    get_vault_dir(tmp_base).mkdir(parents=True, exist_ok=True)
    assert check_rotation_due(tmp_base) is None
