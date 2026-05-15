"""Schema enforcement for .env profiles — validate keys against a defined schema."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _schema_path(base_path: Path, profile: str = "default") -> Path:
    return base_path / ".vault" / profile / "schema.json"


def load_schema(base_path: Path, profile: str = "default") -> dict[str, Any]:
    """Return the schema dict for a profile, or empty dict if none defined."""
    path = _schema_path(base_path, profile)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_schema(base_path: Path, schema: dict[str, Any], profile: str = "default") -> None:
    """Persist a schema dict for a profile."""
    path = _schema_path(base_path, profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2))


def delete_schema(base_path: Path, profile: str = "default") -> bool:
    """Remove the schema file. Returns True if it existed."""
    path = _schema_path(base_path, profile)
    if path.exists():
        path.unlink()
        return True
    return False


def validate_against_schema(
    env: dict[str, str], schema: dict[str, Any]
) -> list[str]:
    """
    Validate *env* against *schema*.

    Schema format example::

        {
          "DATABASE_URL": {"required": true, "type": "url"},
          "DEBUG": {"required": false, "allowed": ["true", "false", "1", "0"]}
        }

    Returns a list of human-readable violation strings (empty == valid).
    """
    violations: list[str] = []

    for key, rules in schema.items():
        required = rules.get("required", False)
        value = env.get(key)

        if required and (value is None or value == ""):
            violations.append(f"{key}: required but missing or empty")
            continue

        if value is None:
            continue

        allowed = rules.get("allowed")
        if allowed and value not in allowed:
            violations.append(
                f"{key}: value {value!r} not in allowed list {allowed}"
            )

        if rules.get("type") == "url" and not (value.startswith("http://") or value.startswith("https://")):
            violations.append(f"{key}: expected a URL but got {value!r}")

        if rules.get("type") == "int":
            try:
                int(value)
            except ValueError:
                violations.append(f"{key}: expected an integer but got {value!r}")

    return violations
