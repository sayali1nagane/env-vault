"""Redaction utilities for masking sensitive env values in output."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

# Patterns that suggest a value is sensitive
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(password|passwd|secret|token|api[_-]?key|private[_-]?key|auth|credential)", re.IGNORECASE),
    re.compile(r"(access[_-]?key|session[_-]?key|signing[_-]?key|encryption[_-]?key)", re.IGNORECASE),
]

REDACT_PLACEHOLDER = "***REDACTED***"


def is_sensitive_key(key: str) -> bool:
    """Return True if the key name suggests a sensitive value."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def redact_value(key: str, value: str, force: bool = False) -> str:
    """Return the redacted placeholder if the key is sensitive, else the original value."""
    if force or is_sensitive_key(key):
        return REDACT_PLACEHOLDER
    return value


def redact_env_dict(
    env: Dict[str, str],
    extra_keys: Optional[List[str]] = None,
    redact_all: bool = False,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values replaced by the placeholder.

    Args:
        env: The environment variable mapping to process.
        extra_keys: Additional key names that should always be redacted.
        redact_all: If True, redact every value regardless of the key name.
    """
    forced: set = set(k.upper() for k in (extra_keys or []))
    return {
        k: redact_value(k, v, force=(redact_all or k.upper() in forced))
        for k, v in env.items()
    }


def format_redacted_table(env: Dict[str, str]) -> str:
    """Format a redacted env dict as a human-readable table string."""
    if not env:
        return "(no variables)"
    width = max(len(k) for k in env)
    lines = [f"{k.ljust(width)}  =  {v}" for k, v in sorted(env.items())]
    return "\n".join(lines)
