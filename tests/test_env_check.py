"""Tests for env_vault.env_check module."""
from __future__ import annotations

import pytest

from env_vault.crypto import generate_key, save_key
from env_vault.storage import init_vault_dir, write_vault
from env_vault.template import save_template
from env_vault.env_check import check_profile_against_template, CheckResult


@pytest.fixture()
def populated_base(tmp_path):
    """Set up a vault with a default profile and a template."""
    base = str(tmp_path)
    init_vault_dir(base_path=base)
    key = generate_key()
    save_key(key, base_path=base, profile="default")
    env_content = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n"
    write_vault(env_content, base_path=base, profile="default", key=key)
    return base


def test_check_returns_ok_when_all_keys_present(populated_base):
    save_template("base", ["DB_HOST", "DB_PORT", "SECRET_KEY"], base_path=populated_base)
    result = check_profile_against_template("base", base_path=populated_base)
    assert isinstance(result, CheckResult)
    assert result.ok


def test_check_detects_missing_key(populated_base):
    save_template("base", ["DB_HOST", "DB_PORT", "SECRET_KEY", "MISSING_KEY"], base_path=populated_base)
    result = check_profile_against_template("base", base_path=populated_base)
    assert not result.ok
    keys = [i.key for i in result.issues]
    assert "MISSING_KEY" in keys


def test_check_detects_empty_value(populated_base):
    key = generate_key()
    save_key(key, base_path=populated_base, profile="staging")
    write_vault("API_KEY=\n", base_path=populated_base, profile="staging", key=key)
    save_template("staging_tpl", ["API_KEY"], base_path=populated_base)
    result = check_profile_against_template("staging_tpl", base_path=populated_base, profile="staging")
    assert not result.ok
    assert result.issues[0].key == "API_KEY"
    assert "empty" in result.issues[0].message


def test_check_missing_vault_reports_all_keys(populated_base):
    save_template("full", ["FOO", "BAR"], base_path=populated_base)
    result = check_profile_against_template("full", base_path=populated_base, profile="nonexistent")
    assert not result.ok
    assert len(result.issues) == 2
    assert {i.key for i in result.issues} == {"FOO", "BAR"}


def test_str_ok_result(populated_base):
    save_template("simple", ["DB_HOST"], base_path=populated_base)
    result = check_profile_against_template("simple", base_path=populated_base)
    assert "✓" in str(result)
    assert "simple" in str(result)


def test_str_failing_result(populated_base):
    save_template("needs_more", ["DB_HOST", "GHOST_KEY"], base_path=populated_base)
    result = check_profile_against_template("needs_more", base_path=populated_base)
    text = str(result)
    assert "✗" in text
    assert "GHOST_KEY" in text
