"""Lint and validate .env file contents for common issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class LintIssue:
    line: int
    key: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line} ({self.key}): {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def summary(self) -> str:
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        return f"{errors} error(s), {warnings} warning(s)"


def lint_env_string(content: str) -> LintResult:
    """Analyse raw .env text and return a LintResult with any issues found."""
    result = LintResult()

    seen_keys: dict[str, int] = {}

    for lineno, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if "=" not in stripped:
            result.issues.append(
                LintIssue(lineno, "<unknown>", "error", "Missing '=' separator")
            )
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip()

        if not key:
            result.issues.append(
                LintIssue(lineno, "<empty>", "error", "Empty key name")
            )
            continue

        if not key.replace("_", "").isalnum() or key[0].isdigit():
            result.issues.append(
                LintIssue(lineno, key, "warning", "Key contains non-standard characters")
            )

        if key != key.upper():
            result.issues.append(
                LintIssue(lineno, key, "info", "Key is not uppercase")
            )

        if key in seen_keys:
            result.issues.append(
                LintIssue(
                    lineno, key, "warning",
                    f"Duplicate key (first seen on line {seen_keys[key]})"
                )
            )
        else:
            seen_keys[key] = lineno

        if not value:
            result.issues.append(
                LintIssue(lineno, key, "info", "Value is empty")
            )

    return result
