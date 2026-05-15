"""Check that all keys in a template are present in the active vault profile."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from env_vault.storage import get_vault_path, get_meta_path, read_vault
from env_vault.crypto import load_key
from env_vault.parser import parse_env_string
from env_vault.template import load_template, list_templates


@dataclass
class CheckIssue:
    key: str
    message: str

    def __str__(self) -> str:
        return f"[MISSING] {self.key}: {self.message}"


@dataclass
class CheckResult:
    template: str
    profile: str
    issues: list[CheckIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def __str__(self) -> str:
        if self.ok:
            return f"✓ Profile '{self.profile}' satisfies template '{self.template}'"
        lines = [f"✗ Profile '{self.profile}' is missing keys from template '{self.template}':\n"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def check_profile_against_template(
    template_name: str,
    base_path: str,
    profile: str = "default",
) -> CheckResult:
    """Return a CheckResult describing which template keys are absent from the vault profile."""
    result = CheckResult(template=template_name, profile=profile)

    template_keys = load_template(template_name, base_path=base_path)

    vault_path = get_vault_path(base_path=base_path, profile=profile)
    if not vault_path.exists():
        for key in template_keys:
            result.issues.append(CheckIssue(key=key, message="vault does not exist for this profile"))
        return result

    key_bytes = load_key(base_path=base_path, profile=profile)
    raw = read_vault(base_path=base_path, profile=profile, key=key_bytes)
    env_dict = parse_env_string(raw)

    for key in template_keys:
        if key not in env_dict:
            result.issues.append(CheckIssue(key=key, message="key not found in vault"))
        elif env_dict[key].strip() == "":
            result.issues.append(CheckIssue(key=key, message="key is present but empty"))

    return result
