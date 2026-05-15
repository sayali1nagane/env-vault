"""Validation rules for env variable values and keys across profiles."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Built-in rule patterns
_URL_RE = re.compile(r'^https?://.+', re.IGNORECASE)
_EMAIL_RE = re.compile(r'^[\w.+-]+@[\w-]+\.[\w.]+$')
_SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+')
_NONEMPTY_RE = re.compile(r'.+')

RULE_PATTERNS: Dict[str, re.Pattern] = {
    "url": _URL_RE,
    "email": _EMAIL_RE,
    "semver": _SEMVER_RE,
    "nonempty": _NONEMPTY_RE,
}


@dataclass
class ValidationIssue:
    key: str
    rule: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message} (rule: {self.rule})"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def validate_env(
    env: Dict[str, str],
    rules: Dict[str, str],
    required_keys: Optional[List[str]] = None,
) -> ValidationResult:
    """Validate *env* dict against a mapping of key -> rule name.

    Args:
        env: Parsed environment variables.
        rules: Mapping of variable name to rule identifier (e.g. ``{"API_URL": "url"}``).
        required_keys: Keys that must be present (non-empty) regardless of rules.

    Returns:
        :class:`ValidationResult` with any issues found.
    """
    result = ValidationResult()

    for key in (required_keys or []):
        if not env.get(key, "").strip():
            result.issues.append(
                ValidationIssue(
                    key=key,
                    rule="required",
                    message="Key is required but missing or empty",
                    severity="error",
                )
            )

    for key, rule_name in rules.items():
        pattern = RULE_PATTERNS.get(rule_name)
        if pattern is None:
            result.issues.append(
                ValidationIssue(
                    key=key,
                    rule=rule_name,
                    message=f"Unknown validation rule '{rule_name}'",
                    severity="warning",
                )
            )
            continue
        value = env.get(key, "")
        if not pattern.match(value):
            result.issues.append(
                ValidationIssue(
                    key=key,
                    rule=rule_name,
                    message=f"Value does not match rule '{rule_name}'",
                    severity="error",
                )
            )

    return result
