"""Rotation reminders and key-age warnings for env-vault."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from env_vault.storage import get_vault_dir

_REMINDER_FILE = "remind.json"
_DEFAULT_INTERVAL_DAYS = 30


def _reminder_path(base_path: Path) -> Path:
    return get_vault_dir(base_path) / _REMINDER_FILE


def get_reminder_config(base_path: Path) -> dict:
    """Return the reminder configuration dict, or sensible defaults."""
    path = _reminder_path(base_path)
    if not path.exists():
        return {"interval_days": _DEFAULT_INTERVAL_DAYS, "enabled": True}
    return json.loads(path.read_text())


def set_reminder_config(base_path: Path, interval_days: int, enabled: bool = True) -> dict:
    """Persist reminder configuration and return it."""
    if interval_days < 1:
        raise ValueError("interval_days must be a positive integer")
    config = {"interval_days": interval_days, "enabled": enabled}
    path = _reminder_path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2))
    return config


def check_rotation_due(base_path: Path, profile: str = "default") -> Optional[int]:
    """Return the number of overdue days if rotation is due, else None.

    Reads the last-rotated timestamp from the vault meta file.
    """
    config = get_reminder_config(base_path)
    if not config.get("enabled", True):
        return None

    meta_path = get_vault_dir(base_path) / profile / "meta.json"
    if not meta_path.exists():
        return None

    meta = json.loads(meta_path.read_text())
    last_rotated_str = meta.get("last_rotated") or meta.get("created_at")
    if not last_rotated_str:
        return None

    last_rotated = datetime.fromisoformat(last_rotated_str)
    if last_rotated.tzinfo is None:
        last_rotated = last_rotated.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    age_days = (now - last_rotated).days
    interval = config.get("interval_days", _DEFAULT_INTERVAL_DAYS)
    overdue = age_days - interval
    return overdue if overdue > 0 else None
