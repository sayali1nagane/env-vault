"""Tests for env_vault.lint module."""

from __future__ import annotations

import pytest

from env_vault.lint import lint_env_string, LintIssue


def test_no_issues_for_valid_env():
    content = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"
    result = lint_env_string(content)
    assert result.issues == []
    assert not result.has_errors
    assert not result.has_warnings


def test_missing_equals_is_error():
    result = lint_env_string("BADLINE\n")
    assert any(i.severity == "error" and "Missing" in i.message for i in result.issues)


def test_empty_key_is_error():
    result = lint_env_string("=somevalue\n")
    assert any(i.severity == "error" and "Empty key" in i.message for i in result.issues)


def test_lowercase_key_is_info():
    result = lint_env_string("my_var=hello\n")
    assert any(i.severity == "info" and "uppercase" in i.message for i in result.issues)


def test_duplicate_key_is_warning():
    content = "FOO=bar\nFOO=baz\n"
    result = lint_env_string(content)
    assert any(i.severity == "warning" and "Duplicate" in i.message for i in result.issues)


def test_empty_value_is_info():
    result = lint_env_string("EMPTY_VAR=\n")
    assert any(i.severity == "info" and "empty" in i.message.lower() for i in result.issues)


def test_comments_and_blanks_are_ignored():
    content = "# This is a comment\n\nVALID=yes\n"
    result = lint_env_string(content)
    assert result.issues == []


def test_has_errors_property():
    result = lint_env_string("BADLINE\n")
    assert result.has_errors


def test_has_warnings_property():
    result = lint_env_string("FOO=1\nFOO=2\n")
    assert result.has_warnings


def test_summary_counts_correctly():
    content = "BADLINE\nFOO=1\nFOO=2\n"
    result = lint_env_string(content)
    summary = result.summary()
    assert "1 error" in summary
    assert "1 warning" in summary


def test_lint_issue_str():
    issue = LintIssue(line=3, key="MY_KEY", severity="warning", message="Something wrong")
    text = str(issue)
    assert "WARNING" in text
    assert "line 3" in text
    assert "MY_KEY" in text
    assert "Something wrong" in text


def test_non_standard_key_characters():
    result = lint_env_string("MY-KEY=value\n")
    assert any("non-standard" in i.message for i in result.issues)
