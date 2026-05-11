"""Key rotation utilities for env-vault."""

import json
from pathlib import Path
from typing import Optional

from .crypto import generate_key, encrypt, decrypt
from .storage import (
    get_vault_dir,
    get_vault_path,
    get_meta_path,
    write_vault,
    read_vault,
    load_key,
    save_key,
)
from .audit import append_audit_entry


def rotate_key(
    project: str,
    base_path: Path,
    old_key: Optional[bytes] = None,
) -> bytes:
    """Rotate the encryption key for a vault.

    Decrypts the existing vault with the old key, generates a new key,
    re-encrypts the vault data, and saves the new key in place.

    Returns the newly generated key.
    """
    vault_path = get_vault_path(project, base_path)
    meta_path = get_meta_path(project, base_path)

    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found for project '{project}'")

    if old_key is None:
        old_key = load_key(project, base_path)

    ciphertext = read_vault(project, base_path)
    plaintext = decrypt(ciphertext, old_key)

    new_key = generate_key()
    new_ciphertext = encrypt(plaintext, new_key)
    write_vault(project, base_path, new_ciphertext)
    save_key(project, base_path, new_key)

    # Update meta with rotation timestamp
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    else:
        meta = {}

    import datetime
    meta["last_rotated"] = datetime.datetime.utcnow().isoformat()
    meta_path.write_text(json.dumps(meta, indent=2))

    append_audit_entry(project, base_path, action="rotate", details={"status": "success"})

    return new_key


def get_rotation_info(project: str, base_path: Path) -> dict:
    """Return metadata about the last key rotation for a project."""
    meta_path = get_meta_path(project, base_path)
    if not meta_path.exists():
        return {"last_rotated": None}
    meta = json.loads(meta_path.read_text())
    return {"last_rotated": meta.get("last_rotated")}
