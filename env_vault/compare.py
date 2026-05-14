"""Compare env variables across profiles."""

from typing import Optional
from env_vault.storage import get_vault_path, get_meta_path, read_vault, load_meta
from env_vault.crypto import load_key
from env_vault.parser import parse_env_string


def _decrypt_profile_env(base_path: str, profile: str) -> dict:
    """Load and decrypt env vars for a given profile."""
    vault_path = get_vault_path(base_path, profile)
    meta_path = get_meta_path(base_path, profile)

    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found for profile '{profile}'")

    from env_vault.crypto import decrypt
    meta = load_meta(meta_path)
    key = load_key(base_path, profile)
    ciphertext = read_vault(vault_path)
    plaintext = decrypt(ciphertext, key)
    return parse_env_string(plaintext)


def compare_profiles(
    base_path: str,
    profile_a: str,
    profile_b: str,
    show_values: bool = False,
) -> dict:
    """
    Compare two profiles and return a dict with:
      - only_in_a: keys present only in profile_a
      - only_in_b: keys present only in profile_b
      - in_both_same: keys present in both with equal values
      - in_both_different: keys present in both with differing values
    """
    env_a = _decrypt_profile_env(base_path, profile_a)
    env_b = _decrypt_profile_env(base_path, profile_b)

    keys_a = set(env_a.keys())
    keys_b = set(env_b.keys())

    only_in_a = sorted(keys_a - keys_b)
    only_in_b = sorted(keys_b - keys_a)
    common = keys_a & keys_b

    in_both_same = []
    in_both_different = []

    for key in sorted(common):
        if env_a[key] == env_b[key]:
            in_both_same.append(key)
        else:
            entry = {"key": key}
            if show_values:
                entry["value_a"] = env_a[key]
                entry["value_b"] = env_b[key]
            in_both_different.append(entry)

    return {
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "in_both_same": in_both_same,
        "in_both_different": in_both_different,
    }
