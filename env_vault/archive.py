"""Archive and restore vault profiles to/from compressed bundles."""

from __future__ import annotations

import json
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from env_vault.storage import get_vault_dir, get_vault_path, get_meta_path, read_vault, write_vault


def _archive_path(base_path: Path, name: str) -> Path:
    archives = base_path / ".env-vault" / "archives"
    archives.mkdir(parents=True, exist_ok=True)
    return archives / f"{name}.tar.gz"


def create_archive(base_path: Path, profile: str, name: str | None = None) -> Path:
    """Compress a vault profile into a .tar.gz archive. Returns the archive path."""
    vault_path = get_vault_path(base_path, profile)
    meta_path = get_meta_path(base_path, profile)

    if not vault_path.exists():
        raise FileNotFoundError(f"No vault found for profile '{profile}'")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_name = name or f"{profile}-{timestamp}"
    dest = _archive_path(base_path, archive_name)

    with tarfile.open(dest, "w:gz") as tar:
        tar.add(vault_path, arcname=f"{profile}.enc")
        if meta_path.exists():
            tar.add(meta_path, arcname=f"{profile}.meta.json")

    return dest


def restore_archive(base_path: Path, archive_path: Path, profile: str | None = None) -> str:
    """Restore a vault profile from a .tar.gz archive. Returns the restored profile name."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(tmp_path)

        enc_files = list(tmp_path.glob("*.enc"))
        if not enc_files:
            raise ValueError("Archive contains no .enc vault file")

        enc_file = enc_files[0]
        detected_profile = profile or enc_file.stem

        dest_vault = get_vault_path(base_path, detected_profile)
        dest_vault.parent.mkdir(parents=True, exist_ok=True)
        dest_vault.write_bytes(enc_file.read_bytes())

        meta_files = list(tmp_path.glob("*.meta.json"))
        if meta_files:
            dest_meta = get_meta_path(base_path, detected_profile)
            dest_meta.write_text(meta_files[0].read_text())

    return detected_profile


def list_archives(base_path: Path) -> list[dict]:
    """List all archives with metadata."""
    archives_dir = base_path / ".env-vault" / "archives"
    if not archives_dir.exists():
        return []

    results = []
    for f in sorted(archives_dir.glob("*.tar.gz")):
        stat = f.stat()
        results.append({
            "name": f.stem.replace(".tar", ""),
            "path": f,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    return results


def delete_archive(base_path: Path, name: str) -> None:
    """Delete a named archive."""
    dest = _archive_path(base_path, name)
    if not dest.exists():
        raise FileNotFoundError(f"Archive '{name}' not found")
    dest.unlink()
