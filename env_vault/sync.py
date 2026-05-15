"""Sync utilities: compare local vault state against a reference .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from env_vault.parser import parse_env_string, serialize_env_dict
from env_vault.storage import get_vault_path, get_meta_path, read_vault, write_vault
from env_vault.crypto import load_key, encrypt, decrypt


@dataclass
class SyncResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.updated)

    def summary(self) -> str:
        lines = []
        for k in self.added:
            lines.append(f"  + {k}")
        for k in self.removed:
            lines.append(f"  - {k}")
        for k in self.updated:
            lines.append(f"  ~ {k}")
        return "\n".join(lines) if lines else "  (no changes)"


def diff_against_file(
    env_file: Path,
    base_path: Path,
    profile: str = "default",
) -> SyncResult:
    """Compare a plaintext .env file against the encrypted vault contents."""
    raw_file = parse_env_string(env_file.read_text())

    vault_path = get_vault_path(base_path, profile)
    if not vault_path.exists():
        return SyncResult(added=list(raw_file.keys()))

    key = load_key(base_path, profile)
    ciphertext = read_vault(base_path, profile)
    plaintext = decrypt(key, ciphertext)
    vault_env = parse_env_string(plaintext.decode())

    result = SyncResult()
    for k, v in raw_file.items():
        if k not in vault_env:
            result.added.append(k)
        elif vault_env[k] != v:
            result.updated.append(k)
    for k in vault_env:
        if k not in raw_file:
            result.removed.append(k)
    return result


def sync_from_file(
    env_file: Path,
    base_path: Path,
    profile: str = "default",
) -> SyncResult:
    """Apply changes from a plaintext .env file into the encrypted vault."""
    result = diff_against_file(env_file, base_path, profile)
    if not result.has_changes:
        return result

    new_env = parse_env_string(env_file.read_text())
    key = load_key(base_path, profile)
    plaintext = serialize_env_dict(new_env).encode()
    ciphertext = encrypt(key, plaintext)
    write_vault(base_path, profile, ciphertext)
    return result
