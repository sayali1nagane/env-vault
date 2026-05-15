"""Pin management: pin specific env keys to fixed values across profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from env_vault.storage import get_vault_dir


def _pin_path(base_path: Path) -> Path:
    return get_vault_dir(base_path) / "pins.json"


def _load(base_path: Path) -> dict:
    p = _pin_path(base_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save(base_path: Path, data: dict) -> None:
    p = _pin_path(base_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def list_pins(base_path: Path) -> dict[str, str]:
    """Return all pinned key->value pairs."""
    return _load(base_path)


def set_pin(base_path: Path, key: str, value: str) -> None:
    """Pin a key to a specific value."""
    if not key:
        raise ValueError("Pin key must not be empty.")
    data = _load(base_path)
    data[key.upper()] = value
    _save(base_path, data)


def remove_pin(base_path: Path, key: str) -> bool:
    """Remove a pinned key. Returns True if it existed."""
    data = _load(base_path)
    key = key.upper()
    if key not in data:
        return False
    del data[key]
    _save(base_path, data)
    return True


def apply_pins(base_path: Path, env_dict: dict[str, str]) -> dict[str, str]:
    """Overlay pinned values onto an env dict, returning a new dict."""
    pins = _load(base_path)
    result = dict(env_dict)
    result.update(pins)
    return result


def get_pin(base_path: Path, key: str) -> Optional[str]:
    """Return the pinned value for a key, or None if not pinned."""
    return _load(base_path).get(key.upper())
