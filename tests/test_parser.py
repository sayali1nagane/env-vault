"""Tests for env_vault.parser module."""

import pytest

from env_vault.parser import (
    parse_env_string,
    serialize_env_dict,
    merge_env_dicts,
    diff_env_dicts,
)


def test_parse_simple_key_value():
    result = parse_env_string("FOO=bar\nBAZ=qux\n")
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_ignores_comments():
    result = parse_env_string("# comment\nKEY=value\n")
    assert result == {"KEY": "value"}


def test_parse_ignores_blank_lines():
    result = parse_env_string("\n\nKEY=value\n\n")
    assert result == {"KEY": "value"}


def test_parse_strips_double_quotes():
    result = parse_env_string('KEY="hello world"')
    assert result["KEY"] == "hello world"


def test_parse_strips_single_quotes():
    result = parse_env_string("KEY='hello world'")
    assert result["KEY"] == "hello world"


def test_parse_value_with_equals_sign():
    result = parse_env_string("KEY=a=b=c")
    assert result["KEY"] == "a=b=c"


def test_parse_ignores_lines_without_equals():
    result = parse_env_string("INVALID_LINE\nKEY=value")
    assert "INVALID_LINE" not in result
    assert result["KEY"] == "value"


def test_serialize_produces_parseable_output():
    original = {"ALPHA": "one", "BETA": "two"}
    serialized = serialize_env_dict(original)
    parsed = parse_env_string(serialized)
    assert parsed == original


def test_serialize_quotes_values_with_spaces():
    serialized = serialize_env_dict({"KEY": "hello world"})
    assert '"hello world"' in serialized


def test_merge_env_dicts_override_takes_precedence():
    base = {"A": "1", "B": "2"}
    override = {"B": "99", "C": "3"}
    result = merge_env_dicts(base, override)
    assert result == {"A": "1", "B": "99", "C": "3"}


def test_diff_env_dicts_detects_added():
    added, removed, changed = diff_env_dicts({}, {"NEW": "val"})
    assert "NEW" in added
    assert removed == []
    assert changed == []


def test_diff_env_dicts_detects_removed():
    added, removed, changed = diff_env_dicts({"OLD": "val"}, {})
    assert "OLD" in removed


def test_diff_env_dicts_detects_changed():
    added, removed, changed = diff_env_dicts({"K": "v1"}, {"K": "v2"})
    assert "K" in changed
    assert added == []
    assert removed == []
