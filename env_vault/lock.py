"""Vault locking — prevent concurrent writes by placing an advisory lock file."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

LOCK_FILENAME = ".vault.lock"
DEFAULT_TIMEOUT = 10  # seconds
STALE_AFTER = 60  # seconds before a lock is considered stale


def _lock_path(base_path: Path) -> Path:
    from env_vault.storage import get_vault_dir
    return get_vault_dir(base_path) / LOCK_FILENAME


def acquire_lock(base_path: Path, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Acquire an advisory lock for the vault.  Raises TimeoutError on failure."""
    lock_file = _lock_path(base_path)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if lock_file.exists():
            try:
                data = json.loads(lock_file.read_text())
                age = time.time() - data.get("ts", 0)
                if age > STALE_AFTER:
                    lock_file.unlink(missing_ok=True)
            except (json.JSONDecodeError, OSError):
                lock_file.unlink(missing_ok=True)

        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                json.dump({"pid": os.getpid(), "ts": time.time()}, fh)
            return
        except FileExistsError:
            time.sleep(0.1)

    raise TimeoutError(
        f"Could not acquire vault lock within {timeout}s. "
        "Another process may be using the vault."
    )


def release_lock(base_path: Path) -> None:
    """Release the advisory lock if it belongs to this process."""
    lock_file = _lock_path(base_path)
    if not lock_file.exists():
        return
    try:
        data = json.loads(lock_file.read_text())
        if data.get("pid") == os.getpid():
            lock_file.unlink(missing_ok=True)
    except (json.JSONDecodeError, OSError):
        lock_file.unlink(missing_ok=True)


def is_locked(base_path: Path) -> bool:
    """Return True if a non-stale lock file exists."""
    lock_file = _lock_path(base_path)
    if not lock_file.exists():
        return False
    try:
        data = json.loads(lock_file.read_text())
        age = time.time() - data.get("ts", 0)
        return age <= STALE_AFTER
    except (json.JSONDecodeError, OSError):
        return False


def lock_info(base_path: Path) -> dict | None:
    """Return lock metadata dict, or None if no active lock."""
    lock_file = _lock_path(base_path)
    if not lock_file.exists():
        return None
    try:
        data = json.loads(lock_file.read_text())
        age = time.time() - data.get("ts", 0)
        if age > STALE_AFTER:
            return None
        data["age_seconds"] = round(age, 1)
        return data
    except (json.JSONDecodeError, OSError):
        return None
