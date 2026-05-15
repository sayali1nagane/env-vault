"""Clone (deep copy) a vault profile to a new base path or profile name."""

from __future__ import annotations

import shutil
from pathlib import Path

from env_vault.storage import (
    get_vault_dir,
    get_vault_path,
    get_meta_path,
    read_vault,
    write_vault,
    read_meta,
    write_meta,
)
from env_vault.audit import append_audit_entry


def clone_profile(
    src_base: Path,
    dst_base: Path,
    src_profile: str = "default",
    dst_profile: str = "default",
) -> Path:
    """Clone an encrypted vault profile from *src* to *dst*.

    Both the encrypted vault file and its metadata are copied.  The
    destination vault directory is created if it does not already exist.
    An audit entry is written to the *destination* vault.

    Returns the destination vault directory path.

    Raises
    ------
    FileNotFoundError
        If the source vault file does not exist.
    FileExistsError
        If the destination vault file already exists.
    """
    src_vault = get_vault_path(src_base, src_profile)
    if not src_vault.exists():
        raise FileNotFoundError(
            f"Source vault not found: {src_vault}"
        )

    dst_vault = get_vault_path(dst_base, dst_profile)
    if dst_vault.exists():
        raise FileExistsError(
            f"Destination vault already exists: {dst_vault}"
        )

    # Ensure destination vault directory exists.
    dst_dir = get_vault_dir(dst_base, dst_profile)
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Copy encrypted blob.
    ciphertext = read_vault(src_base, src_profile)
    write_vault(dst_base, dst_profile, ciphertext)

    # Copy metadata if present.
    src_meta = get_meta_path(src_base, src_profile)
    if src_meta.exists():
        meta = read_meta(src_base, src_profile)
        write_meta(dst_base, dst_profile, meta)

    append_audit_entry(
        dst_base,
        dst_profile,
        action="clone",
        detail={
            "src_base": str(src_base),
            "src_profile": src_profile,
            "dst_profile": dst_profile,
        },
    )

    return dst_dir
