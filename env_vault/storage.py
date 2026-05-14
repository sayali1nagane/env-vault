"""Storage helpers for env-vault vault files and metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def get_vault_dir(base_path: Path, profile: str = "default") -> Path:
    """Return the directory that holds vault files for *profile*."""
    return base_path / ".env-vault" / profile


def get_vault_path(base_path: Path, profile: str = "default") -> Path:
    """Return the path to the encrypted vault file."""
    return get_vault_dir(base_path, profile) / "vault.enc"


def get_meta_path(base_path: Path, profile: str = "default") -> Path:
    """Return the path to the vault metadata JSON file."""
    return get_vault_dir(base_path, profile) / "meta.json"


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_vault_dir(base_path: Path, profile: str = "default") -> Path:
    """Create the vault directory for *profile* if it does not exist."""
    vault_dir = get_vault_dir(base_path, profile)
    vault_dir.mkdir(parents=True, exist_ok=True)
    meta_path = get_meta_path(base_path, profile)
    if not meta_path.exists():
        meta_path.write_text(json.dumps({"profile": profile, "tags": []}), encoding="utf-8")
    return vault_dir


# ---------------------------------------------------------------------------
# Vault read / write
# ---------------------------------------------------------------------------

def write_vault(base_path: Path, data: bytes, profile: str = "default") -> None:
    """Write raw encrypted *data* to the vault file."""
    get_vault_path(base_path, profile).write_bytes(data)


def read_vault(base_path: Path, profile: str = "default") -> bytes:
    """Read raw encrypted bytes from the vault file."""
    path = get_vault_path(base_path, profile)
    if not path.exists():
        raise FileNotFoundError(f"Vault not found: {path}")
    return path.read_bytes()


# ---------------------------------------------------------------------------
# Metadata read / write
# ---------------------------------------------------------------------------

def save_meta(base_path: Path, meta: Dict[str, Any], profile: str = "default") -> None:
    """Persist *meta* dictionary to the profile's meta.json."""
    get_meta_path(base_path, profile).write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )


def load_meta(base_path: Path, profile: str = "default") -> Dict[str, Any]:
    """Load and return the metadata dictionary for *profile*."""
    path = get_meta_path(base_path, profile)
    if not path.exists():
        return {"profile": profile, "tags": []}
    return json.loads(path.read_text(encoding="utf-8"))


def vault_exists(base_path: Path, profile: str = "default") -> bool:
    """Return True if the vault encrypted file exists."""
    return get_vault_path(base_path, profile).exists()
