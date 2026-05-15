"""Tests for env_vault.lock."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from env_vault.lock import (
    LOCK_FILENAME,
    STALE_AFTER,
    acquire_lock,
    is_locked,
    lock_info,
    release_lock,
    _lock_path,
)


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    vault_dir = tmp_path / ".env-vault"
    vault_dir.mkdir()
    return tmp_path


def test_lock_path_is_inside_vault(tmp_base: Path) -> None:
    lp = _lock_path(tmp_base)
    assert lp.name == LOCK_FILENAME
    assert ".env-vault" in str(lp)


def test_acquire_creates_lock_file(tmp_base: Path) -> None:
    acquire_lock(tmp_base)
    assert _lock_path(tmp_base).exists()
    release_lock(tmp_base)


def test_lock_file_contains_pid(tmp_base: Path) -> None:
    acquire_lock(tmp_base)
    data = json.loads(_lock_path(tmp_base).read_text())
    assert data["pid"] == os.getpid()
    release_lock(tmp_base)


def test_is_locked_true_after_acquire(tmp_base: Path) -> None:
    acquire_lock(tmp_base)
    assert is_locked(tmp_base) is True
    release_lock(tmp_base)


def test_is_locked_false_after_release(tmp_base: Path) -> None:
    acquire_lock(tmp_base)
    release_lock(tmp_base)
    assert is_locked(tmp_base) is False


def test_is_locked_false_when_no_file(tmp_base: Path) -> None:
    assert is_locked(tmp_base) is False


def test_acquire_raises_on_timeout(tmp_base: Path) -> None:
    # Write a fresh lock owned by a different pid
    lp = _lock_path(tmp_base)
    lp.write_text(json.dumps({"pid": 99999, "ts": time.time()}))
    with pytest.raises(TimeoutError):
        acquire_lock(tmp_base, timeout=0)
    lp.unlink()


def test_stale_lock_is_overwritten(tmp_base: Path) -> None:
    lp = _lock_path(tmp_base)
    stale_ts = time.time() - (STALE_AFTER + 5)
    lp.write_text(json.dumps({"pid": 99999, "ts": stale_ts}))
    acquire_lock(tmp_base, timeout=2)
    data = json.loads(lp.read_text())
    assert data["pid"] == os.getpid()
    release_lock(tmp_base)


def test_lock_info_returns_none_when_unlocked(tmp_base: Path) -> None:
    assert lock_info(tmp_base) is None


def test_lock_info_returns_dict_when_locked(tmp_base: Path) -> None:
    acquire_lock(tmp_base)
    info = lock_info(tmp_base)
    assert info is not None
    assert "pid" in info
    assert "age_seconds" in info
    release_lock(tmp_base)


def test_release_does_not_remove_foreign_lock(tmp_base: Path) -> None:
    lp = _lock_path(tmp_base)
    lp.write_text(json.dumps({"pid": 99999, "ts": time.time()}))
    release_lock(tmp_base)  # should NOT delete it
    assert lp.exists()
    lp.unlink()
