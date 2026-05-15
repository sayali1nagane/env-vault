"""Access control: per-profile read/write permission flags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

_PERMISSIONS = ("read", "write")


def _access_path(base_path: str, profile: str) -> Path:
    from env_vault.storage import get_vault_dir

    return get_vault_dir(base_path, profile) / "access.json"


def _load(base_path: str, profile: str) -> Dict[str, List[str]]:
    path = _access_path(base_path, profile)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(base_path: str, profile: str, data: Dict[str, List[str]]) -> None:
    path = _access_path(base_path, profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def get_permissions(base_path: str, profile: str, actor: str) -> List[str]:
    """Return the list of permissions granted to *actor* for *profile*."""
    data = _load(base_path, profile)
    return data.get(actor, list(_PERMISSIONS))  # default: full access


def set_permissions(base_path: str, profile: str, actor: str, permissions: List[str]) -> None:
    """Set explicit permissions for *actor* on *profile*."""
    invalid = set(permissions) - set(_PERMISSIONS)
    if invalid:
        raise ValueError(f"Unknown permissions: {', '.join(sorted(invalid))}")
    data = _load(base_path, profile)
    data[actor] = sorted(set(permissions))
    _save(base_path, profile, data)


def revoke_permissions(base_path: str, profile: str, actor: str) -> bool:
    """Remove all explicit permissions for *actor*. Returns True if entry existed."""
    data = _load(base_path, profile)
    if actor not in data:
        return False
    del data[actor]
    _save(base_path, profile, data)
    return True


def list_actors(base_path: str, profile: str) -> Dict[str, List[str]]:
    """Return all actors with explicit permissions on *profile*."""
    return _load(base_path, profile)


def can(base_path: str, profile: str, actor: str, permission: str) -> bool:
    """Return True if *actor* has *permission* on *profile*."""
    return permission in get_permissions(base_path, profile, actor)
