"""Alias management for env-vault profiles.

Allows users to create short, memorable aliases for profile names.
"""

from __future__ import annotations

import json
from pathlib import Path

from env_vault.storage import get_vault_dir


def _alias_path(base_path: str) -> Path:
    return get_vault_dir(base_path) / "aliases.json"


def _load(base_path: str) -> dict[str, str]:
    path = _alias_path(base_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(base_path: str, data: dict[str, str]) -> None:
    path = _alias_path(base_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def list_aliases(base_path: str) -> dict[str, str]:
    """Return all aliases as {alias: profile_name}."""
    return _load(base_path)


def set_alias(base_path: str, alias: str, profile: str) -> None:
    """Create or update an alias pointing to a profile."""
    alias = alias.strip().lower()
    if not alias:
        raise ValueError("Alias must not be empty.")
    if alias == profile:
        raise ValueError("Alias must differ from the profile name.")
    data = _load(base_path)
    data[alias] = profile
    _save(base_path, data)


def remove_alias(base_path: str, alias: str) -> bool:
    """Remove an alias. Returns True if it existed, False otherwise."""
    alias = alias.strip().lower()
    data = _load(base_path)
    if alias not in data:
        return False
    del data[alias]
    _save(base_path, data)
    return True


def resolve_alias(base_path: str, alias_or_profile: str) -> str:
    """Resolve an alias to its profile name, or return the input unchanged."""
    data = _load(base_path)
    return data.get(alias_or_profile.strip().lower(), alias_or_profile)
