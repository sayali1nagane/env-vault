"""Bookmark frequently used key-value pairs for quick reference across profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _bookmark_path(base_path: str) -> Path:
    from env_vault.storage import get_vault_dir
    return get_vault_dir(base_path) / "bookmarks.json"


def _load(base_path: str) -> dict:
    path = _bookmark_path(base_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(base_path: str, data: dict) -> None:
    path = _bookmark_path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def list_bookmarks(base_path: str) -> dict[str, dict]:
    """Return all bookmarks as {name: {key, profile, note}}."""
    return _load(base_path)


def set_bookmark(base_path: str, name: str, key: str, profile: str, note: str = "") -> dict:
    """Create or update a bookmark entry."""
    name = name.lower().strip()
    if not name:
        raise ValueError("Bookmark name must not be empty.")
    data = _load(base_path)
    data[name] = {"key": key.upper(), "profile": profile, "note": note}
    _save(base_path, data)
    return data[name]


def get_bookmark(base_path: str, name: str) -> Optional[dict]:
    """Return a single bookmark or None if not found."""
    return _load(base_path).get(name.lower().strip())


def remove_bookmark(base_path: str, name: str) -> bool:
    """Remove a bookmark by name. Returns True if it existed."""
    data = _load(base_path)
    key = name.lower().strip()
    if key not in data:
        return False
    del data[key]
    _save(base_path, data)
    return True


def find_bookmarks_for_key(base_path: str, key: str) -> list[dict]:
    """Return all bookmarks referencing a specific env key (case-insensitive)."""
    upper = key.upper()
    return [
        {"name": name, **entry}
        for name, entry in _load(base_path).items()
        if entry["key"] == upper
    ]
