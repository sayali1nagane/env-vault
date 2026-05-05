"""Parser module for reading and writing .env file content."""

from typing import Dict, List, Tuple


def parse_env_string(content: str) -> Dict[str, str]:
    """Parse a .env formatted string into a dictionary of key-value pairs."""
    result: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes if present
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        if key:
            result[key] = value
    return result


def serialize_env_dict(env_vars: Dict[str, str]) -> str:
    """Serialize a dictionary of key-value pairs into a .env formatted string."""
    lines: List[str] = []
    for key, value in sorted(env_vars.items()):
        # Quote values containing spaces or special characters
        if any(c in value for c in (" ", "#", "'", '"', "\n")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def merge_env_dicts(
    base: Dict[str, str], override: Dict[str, str]
) -> Dict[str, str]:
    """Merge two env dictionaries, with override taking precedence."""
    merged = dict(base)
    merged.update(override)
    return merged


def diff_env_dicts(
    old: Dict[str, str], new: Dict[str, str]
) -> Tuple[List[str], List[str], List[str]]:
    """Return (added, removed, changed) key lists between two env dicts."""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = sorted(k for k in old_keys & new_keys if old[k] != new[k])
    return added, removed, changed
