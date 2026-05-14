"""Tag management for env-vault: attach, remove, and filter vaults by tags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from env_vault.storage import get_meta_path, load_meta, save_meta


def get_tags(base_path: Path, profile: str = "default") -> List[str]:
    """Return the list of tags for the given profile vault."""
    meta = load_meta(base_path, profile)
    return meta.get("tags", [])


def add_tag(base_path: Path, tag: str, profile: str = "default") -> List[str]:
    """Add a tag to the vault metadata. Returns updated tag list."""
    meta = load_meta(base_path, profile)
    tags: List[str] = meta.get("tags", [])
    tag = tag.strip().lower()
    if not tag:
        raise ValueError("Tag must not be empty.")
    if tag not in tags:
        tags.append(tag)
        meta["tags"] = tags
        save_meta(base_path, meta, profile)
    return tags


def remove_tag(base_path: Path, tag: str, profile: str = "default") -> List[str]:
    """Remove a tag from the vault metadata. Returns updated tag list."""
    meta = load_meta(base_path, profile)
    tags: List[str] = meta.get("tags", [])
    tag = tag.strip().lower()
    if tag not in tags:
        raise KeyError(f"Tag '{tag}' not found.")
    tags.remove(tag)
    meta["tags"] = tags
    save_meta(base_path, meta, profile)
    return tags


def list_profiles_by_tag(base_path: Path, tag: str) -> List[str]:
    """Return all profile names whose vault metadata contains the given tag."""
    tag = tag.strip().lower()
    matched: List[str] = []
    vault_root = base_path / ".env-vault"
    if not vault_root.exists():
        return matched
    for profile_dir in sorted(vault_root.iterdir()):
        if not profile_dir.is_dir():
            continue
        profile = profile_dir.name
        try:
            tags = get_tags(base_path, profile)
            if tag in tags:
                matched.append(profile)
        except Exception:
            continue
    return matched
