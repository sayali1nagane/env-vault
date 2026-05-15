"""Tests for env_vault.pin module."""

from __future__ import annotations

import pytest
from pathlib import Path

from click.testing import CliRunner

from env_vault.pin import list_pins, set_pin, remove_pin, apply_pins, get_pin
from env_vault.cli_pin import pin_group


@pytest.fixture()
def tmp_base(tmp_path: Path) -> Path:
    return tmp_path


def test_list_pins_empty_by_default(tmp_base):
    assert list_pins(tmp_base) == {}


def test_set_pin_creates_entry(tmp_base):
    set_pin(tmp_base, "DB_HOST", "localhost")
    assert list_pins(tmp_base)["DB_HOST"] == "localhost"


def test_set_pin_normalises_key_to_uppercase(tmp_base):
    set_pin(tmp_base, "db_host", "localhost")
    pins = list_pins(tmp_base)
    assert "DB_HOST" in pins
    assert "db_host" not in pins


def test_set_pin_overwrites_existing(tmp_base):
    set_pin(tmp_base, "KEY", "first")
    set_pin(tmp_base, "KEY", "second")
    assert list_pins(tmp_base)["KEY"] == "second"


def test_set_pin_empty_key_raises(tmp_base):
    with pytest.raises(ValueError):
        set_pin(tmp_base, "", "value")


def test_remove_pin_returns_true_when_exists(tmp_base):
    set_pin(tmp_base, "FOO", "bar")
    result = remove_pin(tmp_base, "FOO")
    assert result is True
    assert "FOO" not in list_pins(tmp_base)


def test_remove_pin_returns_false_when_missing(tmp_base):
    result = remove_pin(tmp_base, "NONEXISTENT")
    assert result is False


def test_get_pin_returns_value(tmp_base):
    set_pin(tmp_base, "SECRET", "abc123")
    assert get_pin(tmp_base, "SECRET") == "abc123"


def test_get_pin_returns_none_when_missing(tmp_base):
    assert get_pin(tmp_base, "MISSING") is None


def test_apply_pins_overlays_values(tmp_base):
    set_pin(tmp_base, "HOST", "pinned-host")
    env = {"HOST": "original", "PORT": "5432"}
    result = apply_pins(tmp_base, env)
    assert result["HOST"] == "pinned-host"
    assert result["PORT"] == "5432"


def test_apply_pins_does_not_mutate_original(tmp_base):
    set_pin(tmp_base, "KEY", "pinned")
    env = {"KEY": "original"}
    apply_pins(tmp_base, env)
    assert env["KEY"] == "original"


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_set_and_list(runner, tmp_base):
    result = runner.invoke(pin_group, ["set", "API_KEY", "secret", "--base", str(tmp_base)])
    assert result.exit_code == 0
    assert "API_KEY" in result.output

    result = runner.invoke(pin_group, ["list", "--base", str(tmp_base)])
    assert "API_KEY" in result.output
    assert "secret" in result.output


def test_cli_remove_cmd(runner, tmp_base):
    runner.invoke(pin_group, ["set", "TMP", "val", "--base", str(tmp_base)])
    result = runner.invoke(pin_group, ["remove", "TMP", "--base", str(tmp_base)])
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_cli_list_empty(runner, tmp_base):
    result = runner.invoke(pin_group, ["list", "--base", str(tmp_base)])
    assert "No pins" in result.output
