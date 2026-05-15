"""Tests for env_vault.validate module and cli_validate commands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from env_vault.validate import (
    ValidationIssue,
    ValidationResult,
    validate_env,
)


# ---------------------------------------------------------------------------
# Unit tests – validate_env
# ---------------------------------------------------------------------------

def test_valid_env_returns_no_issues():
    env = {"API_URL": "https://example.com", "EMAIL": "user@example.com"}
    rules = {"API_URL": "url", "EMAIL": "email"}
    result = validate_env(env, rules)
    assert result.ok()
    assert result.issues == []


def test_invalid_url_produces_error():
    env = {"API_URL": "not-a-url"}
    rules = {"API_URL": "url"}
    result = validate_env(env, rules)
    assert not result.ok()
    assert len(result.errors()) == 1
    assert result.errors()[0].key == "API_URL"
    assert result.errors()[0].rule == "url"


def test_invalid_email_produces_error():
    env = {"EMAIL": "bademail"}
    rules = {"EMAIL": "email"}
    result = validate_env(env, rules)
    assert not result.ok()


def test_required_key_missing_produces_error():
    env = {}
    result = validate_env(env, {}, required_keys=["SECRET_KEY"])
    assert not result.ok()
    issue = result.errors()[0]
    assert issue.key == "SECRET_KEY"
    assert issue.rule == "required"


def test_required_key_empty_string_produces_error():
    env = {"SECRET_KEY": "   "}
    result = validate_env(env, {}, required_keys=["SECRET_KEY"])
    assert not result.ok()


def test_required_key_present_no_issue():
    env = {"SECRET_KEY": "abc123"}
    result = validate_env(env, {}, required_keys=["SECRET_KEY"])
    assert result.ok()


def test_unknown_rule_produces_warning_not_error():
    env = {"FOO": "bar"}
    rules = {"FOO": "nonexistent_rule"}
    result = validate_env(env, rules)
    assert result.ok()  # warnings don't fail
    assert len(result.warnings()) == 1


def test_semver_rule_valid():
    env = {"APP_VERSION": "1.2.3"}
    rules = {"APP_VERSION": "semver"}
    result = validate_env(env, rules)
    assert result.ok()


def test_semver_rule_invalid():
    env = {"APP_VERSION": "v1"}
    rules = {"APP_VERSION": "semver"}
    result = validate_env(env, rules)
    assert not result.ok()


def test_nonempty_rule_passes_for_non_blank():
    env = {"NAME": "alice"}
    rules = {"NAME": "nonempty"}
    result = validate_env(env, rules)
    assert result.ok()


def test_validation_issue_str():
    issue = ValidationIssue(key="FOO", rule="url", message="bad", severity="error")
    text = str(issue)
    assert "ERROR" in text
    assert "FOO" in text
    assert "url" in text


def test_validation_result_errors_and_warnings_split():
    result = ValidationResult(issues=[
        ValidationIssue("A", "url", "bad", "error"),
        ValidationIssue("B", "x", "unknown", "warning"),
    ])
    assert len(result.errors()) == 1
    assert len(result.warnings()) == 1
    assert not result.ok()
