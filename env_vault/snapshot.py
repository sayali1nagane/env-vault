"""Snapshot support: save and restore point-in-time copies of vault data."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from .crypto import load_key, encrypt, decrypt
from .storage import get_vault_dir, read_vault, write_vault


def get_snapshots_dir(base_path: Path) -> Path:
    """Return the directory used to store snapshots."""
    return get_vault_dir(base_path) / "snapshots"


def list_snapshots(base_path: Path) -> list[dict]:
    """Return metadata for all saved snapshots, sorted by creation time."""
    snap_dir = get_snapshots_dir(base_path)
    if not snap_dir.exists():
        return []
    entries = []
    for meta_file in sorted(snap_dir.glob("*.json")):
        try:
            entries.append(json.loads(meta_file.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(entries, key=lambda e: e.get("created_at", 0))


def create_snapshot(base_path: Path, label: Optional[str] = None) -> dict:
    """Create a snapshot of the current vault contents.

    Returns metadata dict for the new snapshot.
    """
    snap_dir = get_snapshots_dir(base_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    key = load_key(base_path)
    ciphertext = read_vault(base_path)  # raw encrypted bytes

    ts = int(time.time())
    snap_id = f"{ts}"
    snap_file = snap_dir / f"{snap_id}.enc"
    meta_file = snap_dir / f"{snap_id}.json"

    snap_file.write_bytes(ciphertext)
    meta = {"id": snap_id, "created_at": ts, "label": label or ""}
    meta_file.write_text(json.dumps(meta))
    return meta


def restore_snapshot(base_path: Path, snap_id: str) -> None:
    """Overwrite the active vault with the contents of a snapshot."""
    snap_dir = get_snapshots_dir(base_path)
    snap_file = snap_dir / f"{snap_id}.enc"
    if not snap_file.exists():
        raise FileNotFoundError(f"Snapshot '{snap_id}' not found.")
    ciphertext = snap_file.read_bytes()
    write_vault(base_path, ciphertext)


def delete_snapshot(base_path: Path, snap_id: str) -> None:
    """Remove a snapshot by id."""
    snap_dir = get_snapshots_dir(base_path)
    for ext in (".enc", ".json"):
        f = snap_dir / f"{snap_id}{ext}"
        if f.exists():
            f.unlink()
