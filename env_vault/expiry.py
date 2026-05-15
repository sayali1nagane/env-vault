"""Key expiry management — set TTL on individual env keys and detect expired ones."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _expiry_path(base_path: str, profile: str = "default") -> Path:
    from env_vault.storage import get_vault_dir
    return get_vault_dir(base_path, profile) / "expiry.json"


def _load(base_path: str, profile: str = "default") -> dict:
    path = _expiry_path(base_path, profile)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save(data: dict, base_path: str, profile: str = "default") -> None:
    path = _expiry_path(base_path, profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_expiry(key: str, expires_at: datetime, base_path: str, profile: str = "default") -> None:
    """Attach an expiry timestamp (UTC) to a key."""
    data = _load(base_path, profile)
    data[key.upper()] = expires_at.astimezone(timezone.utc).isoformat()
    _save(data, base_path, profile)


def remove_expiry(key: str, base_path: str, profile: str = "default") -> bool:
    """Remove expiry for a key. Returns True if the key existed."""
    data = _load(base_path, profile)
    key = key.upper()
    if key not in data:
        return False
    del data[key]
    _save(data, base_path, profile)
    return True


def get_expiry(key: str, base_path: str, profile: str = "default") -> Optional[datetime]:
    """Return the expiry datetime for a key, or None if not set."""
    data = _load(base_path, profile)
    raw = data.get(key.upper())
    if raw is None:
        return None
    return datetime.fromisoformat(raw)


def list_expiries(base_path: str, profile: str = "default") -> dict[str, datetime]:
    """Return all key -> expiry mappings for a profile."""
    data = _load(base_path, profile)
    return {k: datetime.fromisoformat(v) for k, v in data.items()}


def check_expired_keys(base_path: str, profile: str = "default") -> list[str]:
    """Return list of keys whose expiry has passed (as of now UTC)."""
    now = datetime.now(timezone.utc)
    return [
        key
        for key, expires_at in list_expiries(base_path, profile).items()
        if expires_at <= now
    ]
