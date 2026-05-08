"""Export and import utilities for env-vault encrypted files."""

import json
import base64
from pathlib import Path
from typing import Optional

from env_vault.crypto import encrypt, decrypt, load_key
from env_vault.parser import parse_env_string, serialize_env_dict
from env_vault.storage import get_vault_path, get_meta_path, read_vault


def export_vault(project_name: str, output_path: Path, base_path: Path = Path.home()) -> None:
    """Export an encrypted vault to a portable bundle file."""
    vault_path = get_vault_path(project_name, base_path)
    meta_path = get_meta_path(project_name, base_path)

    if not vault_path.exists():
        raise FileNotFoundError(f"Vault for '{project_name}' not found.")

    encrypted_data = vault_path.read_bytes()
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())

    bundle = {
        "project": project_name,
        "version": 1,
        "encrypted": base64.b64encode(encrypted_data).decode("utf-8"),
        "meta": meta,
    }

    output_path.write_text(json.dumps(bundle, indent=2))


def import_vault(
    bundle_path: Path,
    base_path: Path = Path.home(),
    overwrite: bool = False,
) -> str:
    """Import a vault bundle file. Returns the project name."""
    if not bundle_path.exists():
        raise FileNotFoundError(f"Bundle file '{bundle_path}' not found.")

    bundle = json.loads(bundle_path.read_text())
    project_name = bundle["project"]
    encrypted_data = base64.b64decode(bundle["encrypted"])
    meta = bundle.get("meta", {})

    vault_path = get_vault_path(project_name, base_path)
    meta_path = get_meta_path(project_name, base_path)

    if vault_path.exists() and not overwrite:
        raise FileExistsError(
            f"Vault for '{project_name}' already exists. Use overwrite=True to replace."
        )

    vault_path.parent.mkdir(parents=True, exist_ok=True)
    vault_path.write_bytes(encrypted_data)
    meta_path.write_text(json.dumps(meta, indent=2))

    return project_name


def decrypt_to_plaintext(project_name: str, base_path: Path = Path.home()) -> str:
    """Decrypt vault contents and return as a plain .env string."""
    key = load_key(project_name, base_path)
    encrypted_data = read_vault(project_name, base_path)
    plaintext = decrypt(encrypted_data, key)
    return plaintext.decode("utf-8")
