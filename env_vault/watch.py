"""File watching utilities for detecting external .env changes."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Optional

from env_vault.storage import get_vault_dir


def _watch_state_path(base_path: Path) -> Path:
    return get_vault_dir(base_path) / "watch_state.json"


def _file_hash(path: Path) -> Optional[str]:
    """Return SHA-256 hex digest of a file, or None if it doesn't exist."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record_watch_state(env_path: Path, base_path: Path) -> dict:
    """Record the current hash and mtime of an .env file."""
    state = {
        "path": str(env_path),
        "hash": _file_hash(env_path),
        "mtime": env_path.stat().st_mtime if env_path.exists() else None,
        "recorded_at": time.time(),
    }
    state_path = _watch_state_path(base_path)
    state_path.write_text(json.dumps(state, indent=2))
    return state


def load_watch_state(base_path: Path) -> Optional[dict]:
    """Load previously recorded watch state, or None if not set."""
    state_path = _watch_state_path(base_path)
    if not state_path.exists():
        return None
    return json.loads(state_path.read_text())


def check_for_changes(env_path: Path, base_path: Path) -> dict:
    """Compare current file state against recorded state.

    Returns a dict with keys:
      - changed (bool)
      - reason (str or None)
      - previous_hash, current_hash
    """
    state = load_watch_state(base_path)
    current_hash = _file_hash(env_path)

    if state is None:
        return {"changed": False, "reason": "no previous state recorded",
                "previous_hash": None, "current_hash": current_hash}

    previous_hash = state.get("hash")

    if previous_hash != current_hash:
        reason = "file deleted" if current_hash is None else "content changed"
        return {"changed": True, "reason": reason,
                "previous_hash": previous_hash, "current_hash": current_hash}

    return {"changed": False, "reason": None,
            "previous_hash": previous_hash, "current_hash": current_hash}


def clear_watch_state(base_path: Path) -> None:
    """Remove the stored watch state file."""
    state_path = _watch_state_path(base_path)
    if state_path.exists():
        state_path.unlink()
