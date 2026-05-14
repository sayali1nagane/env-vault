"""Template management for env-vault.

Allows saving and applying .env templates — skeletons with keys but no
values — so new profiles can be bootstrapped consistently.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .storage import get_vault_dir
from .parser import parse_env_string, serialize_env_dict


def _templates_dir(base_path: Path) -> Path:
    """Return (and create) the templates directory inside the vault."""
    d = get_vault_dir(base_path) / "templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _template_path(base_path: Path, name: str) -> Path:
    return _templates_dir(base_path) / f"{name}.env.template"


def list_templates(base_path: Path) -> List[str]:
    """Return the names of all saved templates."""
    return sorted(
        p.stem.replace(".env", "")
        for p in _templates_dir(base_path).glob("*.env.template")
    )


def save_template(base_path: Path, name: str, keys: List[str]) -> Path:
    """Persist a template with the given key names (values left blank)."""
    if not name or not name.isidentifier():
        raise ValueError(f"Invalid template name: {name!r}")
    skeleton: Dict[str, str] = {k: "" for k in keys}
    path = _template_path(base_path, name)
    path.write_text(serialize_env_dict(skeleton), encoding="utf-8")
    return path


def load_template(base_path: Path, name: str) -> List[str]:
    """Return the list of keys defined in the named template."""
    path = _template_path(base_path, name)
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' does not exist.")
    env = parse_env_string(path.read_text(encoding="utf-8"))
    return list(env.keys())


def delete_template(base_path: Path, name: str) -> None:
    """Remove a saved template."""
    path = _template_path(base_path, name)
    if not path.exists():
        raise FileNotFoundError(f"Template '{name}' does not exist.")
    path.unlink()


def apply_template(base_path: Path, name: str, env: Dict[str, str]) -> Dict[str, str]:
    """Return a new env dict that contains all template keys.

    Existing values from *env* are preserved; missing keys are added with
    an empty string so the caller knows what still needs to be filled in.
    """
    keys = load_template(base_path, name)
    merged = {k: env.get(k, "") for k in keys}
    # Keep any extra keys that were already in env but not in the template
    for k, v in env.items():
        merged.setdefault(k, v)
    return merged
