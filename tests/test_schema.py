"""Tests for env_vault.schema module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from env_vault.schema import (
    delete_schema,
    load_schema,
    save_schema,
    validate_against_schema,
)


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def test_load_schema_returns_empty_when_missing(tmp_base: Path) -> None:
    assert load_schema(tmp_base) == {}


def test_save_and_load_schema_round_trip(tmp_base: Path) -> None:
    schema = {"DATABASE_URL": {"required": True, "type": "url"}}
    save_schema(tmp_base, schema)
    loaded = load_schema(tmp_base)
    assert loaded == schema


def test_save_schema_creates_parent_dirs(tmp_base: Path) -> None:
    schema = {"KEY": {"required": False}}
    save_schema(tmp_base, schema, profile="staging")
    assert (tmp_base / ".vault" / "staging" / "schema.json").exists()


def test_delete_schema_removes_file(tmp_base: Path) -> None:
    save_schema(tmp_base, {"X": {"required": True}})
    result = delete_schema(tmp_base)
    assert result is True
    assert load_schema(tmp_base) == {}


def test_delete_schema_returns_false_when_missing(tmp_base: Path) -> None:
    assert delete_schema(tmp_base) is False


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def test_no_violations_for_valid_env() -> None:
    schema = {"PORT": {"required": True, "type": "int"}}
    env = {"PORT": "8080"}
    assert validate_against_schema(env, schema) == []


def test_required_key_missing_produces_violation() -> None:
    schema = {"DATABASE_URL": {"required": True}}
    violations = validate_against_schema({}, schema)
    assert any("DATABASE_URL" in v for v in violations)


def test_required_key_empty_produces_violation() -> None:
    schema = {"API_KEY": {"required": True}}
    violations = validate_against_schema({"API_KEY": ""}, schema)
    assert any("API_KEY" in v for v in violations)


def test_invalid_url_type_produces_violation() -> None:
    schema = {"CALLBACK": {"type": "url"}}
    violations = validate_against_schema({"CALLBACK": "not-a-url"}, schema)
    assert any("CALLBACK" in v for v in violations)


def test_valid_url_passes() -> None:
    schema = {"CALLBACK": {"type": "url"}}
    assert validate_against_schema({"CALLBACK": "https://example.com"}, schema) == []


def test_invalid_int_type_produces_violation() -> None:
    schema = {"WORKERS": {"type": "int"}}
    violations = validate_against_schema({"WORKERS": "many"}, schema)
    assert any("WORKERS" in v for v in violations)


def test_valid_int_passes() -> None:
    schema = {"WORKERS": {"type": "int"}}
    assert validate_against_schema({"WORKERS": "4"}, schema) == []


def test_allowed_values_rejects_unknown() -> None:
    schema = {"ENV": {"allowed": ["dev", "prod", "staging"]}}
    violations = validate_against_schema({"ENV": "test"}, schema)
    assert any("ENV" in v for v in violations)


def test_allowed_values_accepts_valid() -> None:
    schema = {"ENV": {"allowed": ["dev", "prod"]}}
    assert validate_against_schema({"ENV": "prod"}, schema) == []


def test_optional_missing_key_no_violation() -> None:
    schema = {"OPTIONAL_KEY": {"required": False, "type": "int"}}
    assert validate_against_schema({}, schema) == []
