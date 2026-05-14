"""Tests for env_vault.snapshot and env_vault.cli_snapshot."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from pathlib import Path

from env_vault.crypto import generate_key, save_key, encrypt
from env_vault.storage import init_vault_dir, write_vault
from env_vault.snapshot import (
    get_snapshots_dir,
    list_snapshots,
    create_snapshot,
    restore_snapshot,
    delete_snapshot,
)
from env_vault.cli_snapshot import snapshot_group


@pytest.fixture()
def populated_vault(tmp_path: Path) -> Path:
    init_vault_dir(tmp_path)
    key = generate_key()
    save_key(tmp_path, key)
    ciphertext = encrypt(key, b"DB_HOST=localhost\nDB_PORT=5432\n")
    write_vault(tmp_path, ciphertext)
    return tmp_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


# --- unit tests ---

def test_get_snapshots_dir_is_inside_vault(populated_vault: Path) -> None:
    snap_dir = get_snapshots_dir(populated_vault)
    assert ".env-vault" in str(snap_dir)
    assert snap_dir.name == "snapshots"


def test_list_snapshots_empty_when_none(populated_vault: Path) -> None:
    assert list_snapshots(populated_vault) == []


def test_create_snapshot_returns_metadata(populated_vault: Path) -> None:
    meta = create_snapshot(populated_vault, label="initial")
    assert "id" in meta
    assert meta["label"] == "initial"
    assert isinstance(meta["created_at"], int)


def test_create_snapshot_writes_files(populated_vault: Path) -> None:
    meta = create_snapshot(populated_vault)
    snap_dir = get_snapshots_dir(populated_vault)
    assert (snap_dir / f"{meta['id']}.enc").exists()
    assert (snap_dir / f"{meta['id']}.json").exists()


def test_list_snapshots_returns_all(populated_vault: Path) -> None:
    create_snapshot(populated_vault, label="snap1")
    create_snapshot(populated_vault, label="snap2")
    snaps = list_snapshots(populated_vault)
    assert len(snaps) == 2
    labels = {s["label"] for s in snaps}
    assert labels == {"snap1", "snap2"}


def test_restore_snapshot_overwrites_vault(populated_vault: Path) -> None:
    from env_vault.crypto import load_key, decrypt
    from env_vault.storage import read_vault

    key = load_key(populated_vault)
    meta = create_snapshot(populated_vault)

    # overwrite vault with different data
    new_cipher = encrypt(key, b"NEW=value\n")
    write_vault(populated_vault, new_cipher)

    restore_snapshot(populated_vault, meta["id"])
    restored = decrypt(key, read_vault(populated_vault))
    assert b"DB_HOST" in restored


def test_restore_snapshot_missing_raises(populated_vault: Path) -> None:
    with pytest.raises(FileNotFoundError):
        restore_snapshot(populated_vault, "nonexistent")


def test_delete_snapshot_removes_files(populated_vault: Path) -> None:
    meta = create_snapshot(populated_vault)
    snap_dir = get_snapshots_dir(populated_vault)
    delete_snapshot(populated_vault, meta["id"])
    assert not (snap_dir / f"{meta['id']}.enc").exists()
    assert not (snap_dir / f"{meta['id']}.json").exists()


# --- CLI tests ---

def test_cli_save_creates_snapshot(runner: CliRunner, populated_vault: Path) -> None:
    result = runner.invoke(snapshot_group, ["save", "--base", str(populated_vault), "--label", "cli-test"])
    assert result.exit_code == 0
    assert "Snapshot saved" in result.output


def test_cli_list_shows_snapshots(runner: CliRunner, populated_vault: Path) -> None:
    create_snapshot(populated_vault, label="listed")
    result = runner.invoke(snapshot_group, ["list", "--base", str(populated_vault)])
    assert result.exit_code == 0
    assert "listed" in result.output


def test_cli_restore_with_yes_flag(runner: CliRunner, populated_vault: Path) -> None:
    meta = create_snapshot(populated_vault)
    result = runner.invoke(snapshot_group, ["restore", meta["id"], "--base", str(populated_vault), "--yes"])
    assert result.exit_code == 0
    assert "restored" in result.output


def test_cli_delete_with_yes_flag(runner: CliRunner, populated_vault: Path) -> None:
    meta = create_snapshot(populated_vault)
    result = runner.invoke(snapshot_group, ["delete", meta["id"], "--base", str(populated_vault), "--yes"])
    assert result.exit_code == 0
    assert "deleted" in result.output
