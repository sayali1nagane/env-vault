"""Per-key inline notes/annotations stored alongside vault metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from env_vault.storage import get_vault_dir


def _notes_path(base_path: str, profile: str = "default") -> Path:
    return get_vault_dir(base_path, profile) / "notes.json"


def _load(base_path: str, profile: str = "default") -> Dict[str, str]:
    path = _notes_path(base_path, profile)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(data: Dict[str, str], base_path: str, profile: str = "default") -> None:
    path = _notes_path(base_path, profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_note(key: str, base_path: str, profile: str = "default") -> Optional[str]:
    """Return the note for *key*, or None if no note exists."""
    return _load(base_path, profile).get(key.upper())


def set_note(key: str, note: str, base_path: str, profile: str = "default") -> None:
    """Attach *note* to *key*.  An empty string clears the note."""
    data = _load(base_path, profile)
    if note == "":
        data.pop(key.upper(), None)
    else:
        data[key.upper()] = note
    _save(data, base_path, profile)


def remove_note(key: str, base_path: str, profile: str = "default") -> bool:
    """Remove the note for *key*.  Returns True if a note existed."""
    data = _load(base_path, profile)
    existed = key.upper() in data
    data.pop(key.upper(), None)
    _save(data, base_path, profile)
    return existed


def list_notes(base_path: str, profile: str = "default") -> Dict[str, str]:
    """Return all key→note mappings for the given profile."""
    return dict(_load(base_path, profile))


def clear_notes(base_path: str, profile: str = "default") -> int:
    """Delete all notes for the profile.  Returns the number removed."""
    data = _load(base_path, profile)
    count = len(data)
    _save({}, base_path, profile)
    return count
