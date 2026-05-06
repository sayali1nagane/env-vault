"""Tests for the env_vault.crypto module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from env_vault.crypto import (
    generate_key,
    derive_key_from_passphrase,
    encrypt,
    decrypt,
    save_key,
    load_key,
)


def test_generate_key_returns_bytes():
    key = generate_key()
    assert isinstance(key, bytes)
    assert len(key) == 44  # Base64-encoded 32-byte Fernet key


def test_generate_key_is_unique():
    """Each call to generate_key should produce a different key."""
    key1 = generate_key()
    key2 = generate_key()
    assert key1 != key2


def test_derive_key_from_passphrase_deterministic():
    salt = b"testsalt12345678"
    key1 = derive_key_from_passphrase("mysecret", salt)
    key2 = derive_key_from_passphrase("mysecret", salt)
    assert key1 == key2


def test_derive_key_different_passphrases():
    salt = b"testsalt12345678"
    key1 = derive_key_from_passphrase("secret1", salt)
    key2 = derive_key_from_passphrase("secret2", salt)
    assert key1 != key2


def test_derive_key_different_salts():
    """The same passphrase with different salts should produce different keys."""
    key1 = derive_key_from_passphrase("mysecret", b"salt1salt1salt1a")
    key2 = derive_key_from_passphrase("mysecret", b"salt2salt2salt2b")
    assert key1 != key2


def test_encrypt_decrypt_roundtrip():
    key = generate_key()
    original = "DATABASE_URL=postgres://localhost/mydb"
    ciphertext = encrypt(original, key)
    assert ciphertext != original.encode()
    recovered = decrypt(ciphertext, key)
    assert recovered == original


def test_encrypt_produces_different_ciphertext_each_time():
    key = generate_key()
    plaintext = "SECRET_KEY=abc123"
    ct1 = encrypt(plaintext, key)
    ct2 = encrypt(plaintext, key)
    assert ct1 != ct2  # Fernet uses random IV


def test_decrypt_with_wrong_key_raises():
    from cryptography.fernet import InvalidToken
    key1 = generate_key()
    key2 = generate_key()
    ciphertext = encrypt("some value", key1)
    with pytest.raises(InvalidToken):
        decrypt(ciphertext, key2)


def test_save_and_load_key(tmp_path):
    key = generate_key()
    with patch("env_vault.crypto.KEY_DIR", tmp_path):
        saved_path = save_key("myproject", key)
        assert saved_path.exists()
        loaded = load_key("myproject")
    assert loaded == key


def test_load_key_missing_raises(tmp_path):
    with patch("env_vault.crypto.KEY_DIR", tmp_path):
        with pytest.raises(FileNotFoundError, match="myproject"):
            load_key("myproject")
