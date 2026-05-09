"""Audit log for tracking vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_FILENAME = "audit.log"


def get_audit_path(base_path: Path) -> Path:
    """Return the path to the audit log file."""
    from env_vault.storage import get_vault_dir
    return get_vault_dir(base_path) / AUDIT_FILENAME


def append_audit_entry(
    base_path: Path,
    action: str,
    details: Optional[dict] = None,
) -> None:
    """Append a single audit log entry as a JSON line."""
    audit_path = get_audit_path(base_path)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "details": details or {},
    }
    with audit_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_audit_log(base_path: Path) -> list[dict]:
    """Read all audit log entries from the log file."""
    audit_path = get_audit_path(base_path)
    if not audit_path.exists():
        return []
    entries = []
    with audit_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def format_audit_log(entries: list[dict]) -> str:
    """Format audit log entries for human-readable display."""
    if not entries:
        return "No audit log entries found."
    lines = []
    for entry in entries:
        ts = entry.get("timestamp", "unknown")
        action = entry.get("action", "unknown")
        user = entry.get("user", "unknown")
        details = entry.get("details", {})
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        line = f"[{ts}] {user}: {action}"
        if detail_str:
            line += f" ({detail_str})"
        lines.append(line)
    return "\n".join(lines)
