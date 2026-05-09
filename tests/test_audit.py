"""Tests for env_vault.audit module."""

import json
import pytest
from pathlib import Path

from env_vault.audit import (
    get_audit_path,
    append_audit_entry,
    read_audit_log,
    format_audit_log,
)
from env_vault.storage import init_vault_dir


@pytest.fixture
def tmp_base(tmp_path):
    init_vault_dir(tmp_path)
    return tmp_path


def test_get_audit_path_returns_path(tmp_base):
    path = get_audit_path(tmp_base)
    assert path.name == "audit.log"
    assert ".env-vault" in str(path)


def test_append_creates_log_file(tmp_base):
    append_audit_entry(tmp_base, "init")
    assert get_audit_path(tmp_base).exists()


def test_append_writes_valid_json(tmp_base):
    append_audit_entry(tmp_base, "set", {"key": "API_KEY"})
    audit_path = get_audit_path(tmp_base)
    line = audit_path.read_text().strip()
    entry = json.loads(line)
    assert entry["action"] == "set"
    assert entry["details"]["key"] == "API_KEY"
    assert "timestamp" in entry
    assert "user" in entry


def test_read_audit_log_empty_when_no_file(tmp_base):
    entries = read_audit_log(tmp_base)
    assert entries == []


def test_read_audit_log_returns_all_entries(tmp_base):
    append_audit_entry(tmp_base, "init")
    append_audit_entry(tmp_base, "set", {"key": "FOO"})
    append_audit_entry(tmp_base, "get", {"key": "FOO"})
    entries = read_audit_log(tmp_base)
    assert len(entries) == 3
    assert entries[0]["action"] == "init"
    assert entries[2]["action"] == "get"


def test_format_audit_log_no_entries():
    result = format_audit_log([])
    assert "No audit log" in result


def test_format_audit_log_with_entries(tmp_base):
    append_audit_entry(tmp_base, "export", {"file": "bundle.zip"})
    entries = read_audit_log(tmp_base)
    output = format_audit_log(entries)
    assert "export" in output
    assert "bundle.zip" in output


def test_multiple_appends_are_separate_lines(tmp_base):
    append_audit_entry(tmp_base, "init")
    append_audit_entry(tmp_base, "set")
    raw = get_audit_path(tmp_base).read_text().strip().splitlines()
    assert len(raw) == 2
    for line in raw:
        json.loads(line)  # must not raise
