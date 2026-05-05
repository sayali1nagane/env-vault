"""Storage module for managing encrypted .env vault files."""

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_VAULT_DIR = ".env-vault"
DEFAULT_VAULT_FILE = "vault.enc"
DEFAULT_META_FILE = "meta.json"


def get_vault_dir(base_path: Optional[Path] = None) -> Path:
    """Return the vault directory path relative to the given base path."""
    base = base_path or Path.cwd()
    return base / DEFAULT_VAULT_DIR


def get_vault_path(base_path: Optional[Path] = None) -> Path:
    """Return the full path to the encrypted vault file."""
    return get_vault_dir(base_path) / DEFAULT_VAULT_FILE


def get_meta_path(base_path: Optional[Path] = None) -> Path:
    """Return the full path to the vault metadata file."""
    return get_vault_dir(base_path) / DEFAULT_META_FILE


def init_vault_dir(base_path: Optional[Path] = None) -> Path:
    """Create the vault directory if it does not exist."""
    vault_dir = get_vault_dir(base_path)
    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir


def write_vault(ciphertext: bytes, base_path: Optional[Path] = None) -> Path:
    """Write encrypted ciphertext to the vault file."""
    init_vault_dir(base_path)
    vault_path = get_vault_path(base_path)
    vault_path.write_bytes(ciphertext)
    return vault_path


def read_vault(base_path: Optional[Path] = None) -> bytes:
    """Read and return the raw bytes from the vault file."""
    vault_path = get_vault_path(base_path)
    if not vault_path.exists():
        raise FileNotFoundError(f"Vault file not found: {vault_path}")
    return vault_path.read_bytes()


def write_meta(meta: dict, base_path: Optional[Path] = None) -> Path:
    """Write metadata dictionary as JSON to the meta file."""
    init_vault_dir(base_path)
    meta_path = get_meta_path(base_path)
    meta_path.write_text(json.dumps(meta, indent=2))
    return meta_path


def read_meta(base_path: Optional[Path] = None) -> dict:
    """Read and return the metadata dictionary from the meta file."""
    meta_path = get_meta_path(base_path)
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text())


def vault_exists(base_path: Optional[Path] = None) -> bool:
    """Return True if the vault file exists."""
    return get_vault_path(base_path).exists()
