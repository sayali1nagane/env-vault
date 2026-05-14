"""Track per-key change history across vault operations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from env_vault.storage import get_vault_dir


def get_history_path(base_path: Path, profile: str = "default") -> Path:
    """Return path to the history file for a given profile."""
    return get_vault_dir(base_path, profile) / "history.json"


def _load_raw(base_path: Path, profile: str) -> dict[str, list[dict[str, Any]]]:
    path = get_history_path(base_path, profile)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_raw(base_path: Path, profile: str, data: dict[str, list[dict[str, Any]]]) -> None:
    path = get_history_path(base_path, profile)
    path.write_text(json.dumps(data, indent=2))


def record_change(
    base_path: Path,
    key: str,
    old_value: str | None,
    new_value: str | None,
    profile: str = "default",
    actor: str = "cli",
) -> None:
    """Append a change entry for *key* to the history log."""
    data = _load_raw(base_path, profile)
    entries = data.setdefault(key, [])
    entries.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old": old_value,
            "new": new_value,
            "actor": actor,
        }
    )
    _save_raw(base_path, profile, data)


def get_key_history(
    base_path: Path, key: str, profile: str = "default"
) -> list[dict[str, Any]]:
    """Return all recorded changes for *key*, oldest first."""
    return _load_raw(base_path, profile).get(key, [])


def clear_key_history(
    base_path: Path, key: str, profile: str = "default"
) -> None:
    """Remove all history entries for *key*."""
    data = _load_raw(base_path, profile)
    data.pop(key, None)
    _save_raw(base_path, profile, data)


def list_tracked_keys(base_path: Path, profile: str = "default") -> list[str]:
    """Return keys that have at least one history entry."""
    return sorted(_load_raw(base_path, profile).keys())
