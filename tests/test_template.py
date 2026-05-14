"""Tests for env_vault.template."""

from __future__ import annotations

import pytest
from pathlib import Path

from env_vault.template import (
    list_templates,
    save_template,
    load_template,
    delete_template,
    apply_template,
)


@pytest.fixture
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path


def test_list_templates_empty_by_default(tmp_base):
    assert list_templates(tmp_base) == []


def test_save_template_creates_file(tmp_base):
    path = save_template(tmp_base, "base", ["DB_URL", "SECRET_KEY"])
    assert path.exists()
    assert path.name == "base.env.template"


def test_save_template_appears_in_list(tmp_base):
    save_template(tmp_base, "base", ["DB_URL"])
    save_template(tmp_base, "minimal", ["APP_ENV"])
    assert list_templates(tmp_base) == ["base", "minimal"]


def test_load_template_returns_keys(tmp_base):
    save_template(tmp_base, "web", ["PORT", "HOST", "DEBUG"])
    keys = load_template(tmp_base, "web")
    assert set(keys) == {"PORT", "HOST", "DEBUG"}


def test_load_template_missing_raises(tmp_base):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_template(tmp_base, "ghost")


def test_delete_template_removes_file(tmp_base):
    save_template(tmp_base, "temp", ["FOO"])
    delete_template(tmp_base, "temp")
    assert list_templates(tmp_base) == []


def test_delete_template_missing_raises(tmp_base):
    with pytest.raises(FileNotFoundError):
        delete_template(tmp_base, "nope")


def test_save_template_invalid_name_raises(tmp_base):
    with pytest.raises(ValueError, match="Invalid template name"):
        save_template(tmp_base, "bad name!", ["KEY"])


def test_apply_template_adds_missing_keys(tmp_base):
    save_template(tmp_base, "api", ["API_KEY", "API_URL", "TIMEOUT"])
    existing = {"API_KEY": "abc123"}
    result = apply_template(tmp_base, "api", existing)
    assert result["API_KEY"] == "abc123"  # preserved
    assert result["API_URL"] == ""        # added blank
    assert result["TIMEOUT"] == ""        # added blank


def test_apply_template_preserves_extra_keys(tmp_base):
    save_template(tmp_base, "slim", ["A"])
    existing = {"A": "1", "B": "2"}
    result = apply_template(tmp_base, "slim", existing)
    assert result["B"] == "2"


def test_apply_template_no_changes_when_complete(tmp_base):
    save_template(tmp_base, "full", ["X", "Y"])
    existing = {"X": "1", "Y": "2"}
    result = apply_template(tmp_base, "full", existing)
    assert result == {"X": "1", "Y": "2"}
