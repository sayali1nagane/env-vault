"""Search and filter env keys across profiles."""

from __future__ import annotations

from typing import Optional

from env_vault.storage import get_vault_path, get_meta_path, read_vault, list_profiles
from env_vault.crypto import load_key
from env_vault.parser import parse_env_string


def search_keys(
    pattern: str,
    base_path: str = ".",
    profile: Optional[str] = None,
    keys_only: bool = False,
) -> dict[str, dict[str, str]]:
    """Search for env keys matching *pattern* (case-insensitive substring).

    Returns a mapping of ``profile_name -> {key: value}`` for every match.
    If *profile* is given, only that profile is searched.
    If *keys_only* is True, values are replaced with ``"***"``.
    """
    profiles_to_search: list[str]
    if profile:
        profiles_to_search = [profile]
    else:
        try:
            profiles_to_search = list_profiles(base_path)
        except FileNotFoundError:
            profiles_to_search = []
        if not profiles_to_search:
            profiles_to_search = ["default"]

    pattern_lower = pattern.lower()
    results: dict[str, dict[str, str]] = {}

    for prof in profiles_to_search:
        vault_path = get_vault_path(base_path, prof)
        if not vault_path.exists():
            continue
        try:
            key = load_key(base_path, prof)
            ciphertext = read_vault(base_path, prof)
            from env_vault.crypto import decrypt
            plaintext = decrypt(ciphertext, key)
            env_dict = parse_env_string(plaintext)
        except Exception:
            continue

        matches = {
            k: ("***" if keys_only else v)
            for k, v in env_dict.items()
            if pattern_lower in k.lower()
        }
        if matches:
            results[prof] = matches

    return results


def find_key_in_profiles(
    key: str,
    base_path: str = ".",
) -> list[str]:
    """Return a list of profile names that contain the exact *key*."""
    results = search_keys(key, base_path=base_path, keys_only=True)
    return [
        prof
        for prof, matches in results.items()
        if key in matches
    ]
