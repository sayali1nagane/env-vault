"""Tests for env_vault.redact and env_vault.cli_redact."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from env_vault.redact import (
    is_sensitive_key,
    redact_value,
    redact_env_dict,
    format_redacted_table,
    REDACT_PLACEHOLDER,
)


# ---------------------------------------------------------------------------
# Unit tests for redact.py
# ---------------------------------------------------------------------------

def test_is_sensitive_key_detects_password():
    assert is_sensitive_key("DB_PASSWORD") is True


def test_is_sensitive_key_detects_token():
    assert is_sensitive_key("GITHUB_TOKEN") is True


def test_is_sensitive_key_detects_api_key():
    assert is_sensitive_key("STRIPE_API_KEY") is True


def test_is_sensitive_key_ignores_safe_key():
    assert is_sensitive_key("APP_NAME") is False
    assert is_sensitive_key("PORT") is False


def test_redact_value_masks_sensitive():
    assert redact_value("DB_PASSWORD", "s3cr3t") == REDACT_PLACEHOLDER


def test_redact_value_preserves_safe():
    assert redact_value("APP_ENV", "production") == "production"


def test_redact_value_force_flag():
    assert redact_value("APP_ENV", "production", force=True) == REDACT_PLACEHOLDER


def test_redact_env_dict_masks_sensitive_keys():
    env = {"APP_NAME": "myapp", "API_KEY": "abc123", "SECRET": "xyz"}
    result = redact_env_dict(env)
    assert result["APP_NAME"] == "myapp"
    assert result["API_KEY"] == REDACT_PLACEHOLDER
    assert result["SECRET"] == REDACT_PLACEHOLDER


def test_redact_env_dict_extra_keys():
    env = {"CUSTOM_FIELD": "visible", "ANOTHER": "also_visible"}
    result = redact_env_dict(env, extra_keys=["CUSTOM_FIELD"])
    assert result["CUSTOM_FIELD"] == REDACT_PLACEHOLDER
    assert result["ANOTHER"] == "also_visible"


def test_redact_env_dict_redact_all():
    env = {"APP_NAME": "myapp", "PORT": "8080"}
    result = redact_env_dict(env, redact_all=True)
    assert all(v == REDACT_PLACEHOLDER for v in result.values())


def test_format_redacted_table_empty():
    assert format_redacted_table({}) == "(no variables)"


def test_format_redacted_table_contains_key_and_value():
    output = format_redacted_table({"FOO": "bar"})
    assert "FOO" in output
    assert "bar" in output


def test_format_redacted_table_sorted_output():
    env = {"Z_KEY": "1", "A_KEY": "2"}
    lines = format_redacted_table(env).splitlines()
    assert lines[0].startswith("A_KEY")
    assert lines[1].startswith("Z_KEY")
