"""Encryption and decryption utilities for env-vault using Fernet symmetric encryption."""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


KEY_DIR = Path.home() / ".env-vault" / "keys"


def generate_key() -> bytes:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key()


def derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a passphrase and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def save_key(project_name: str, key: bytes) -> Path:
    """Persist a project key to the local key store."""
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    key_path = KEY_DIR / f"{project_name}.key"
    key_path.write_bytes(key)
    key_path.chmod(0o600)
    return key_path


def load_key(project_name: str) -> bytes:
    """Load a project key from the local key store."""
    key_path = KEY_DIR / f"{project_name}.key"
    if not key_path.exists():
        raise FileNotFoundError(
            f"No key found for project '{project_name}'. "
            f"Run 'env-vault init {project_name}' first."
        )
    return key_path.read_bytes()


def encrypt(plaintext: str, key: bytes) -> bytes:
    """Encrypt a plaintext string and return ciphertext bytes."""
    f = Fernet(key)
    return f.encrypt(plaintext.encode())


def decrypt(ciphertext: bytes, key: bytes) -> str:
    """Decrypt ciphertext bytes and return the plaintext string."""
    f = Fernet(key)
    return f.decrypt(ciphertext).decode()
