"""Profile support for managing multiple named environments (e.g., dev, staging, prod)."""

from pathlib import Path
from typing import List, Optional
import json

from env_vault.storage import (
    get_vault_dir,
    get_vault_path,
    get_meta_path,
    write_vault,
    read_vault,
    write_meta,
    read_meta,
)
from env_vault.crypto import load_key, encrypt, decrypt


DEFAULT_PROFILE = "default"


def list_profiles(base_path: Path) -> List[str]:
    """Return all profile names that have a vault file."""
    vault_dir = get_vault_dir(base_path)
    if not vault_dir.exists():
        return []
    profiles = []
    for f in vault_dir.iterdir():
        if f.suffix == ".enc":
            profiles.append(f.stem)
    return sorted(profiles)


def get_active_profile(base_path: Path) -> str:
    """Read the currently active profile from meta, defaulting to 'default'."""
    meta_path = get_vault_dir(base_path) / "profiles.json"
    if not meta_path.exists():
        return DEFAULT_PROFILE
    data = json.loads(meta_path.read_text())
    return data.get("active", DEFAULT_PROFILE)


def set_active_profile(base_path: Path, profile: str) -> None:
    """Persist the active profile name."""
    vault_dir = get_vault_dir(base_path)
    vault_dir.mkdir(parents=True, exist_ok=True)
    meta_path = vault_dir / "profiles.json"
    existing = {}
    if meta_path.exists():
        existing = json.loads(meta_path.read_text())
    existing["active"] = profile
    meta_path.write_text(json.dumps(existing, indent=2))


def copy_profile(base_path: Path, src: str, dst: str, key: bytes) -> None:
    """Copy encrypted vault data from one profile to another using the same key."""
    src_path = get_vault_dir(base_path) / f"{src}.enc"
    if not src_path.exists():
        raise FileNotFoundError(f"Source profile '{src}' does not exist.")
    dst_path = get_vault_dir(base_path) / f"{dst}.enc"
    ciphertext = src_path.read_bytes()
    plaintext = decrypt(ciphertext, key)
    new_ciphertext = encrypt(plaintext, key)
    dst_path.write_bytes(new_ciphertext)


def delete_profile(base_path: Path, profile: str) -> None:
    """Remove a profile vault file."""
    if profile == DEFAULT_PROFILE:
        raise ValueError("Cannot delete the default profile.")
    vault_path = get_vault_dir(base_path) / f"{profile}.enc"
    if not vault_path.exists():
        raise FileNotFoundError(f"Profile '{profile}' does not exist.")
    vault_path.unlink()
