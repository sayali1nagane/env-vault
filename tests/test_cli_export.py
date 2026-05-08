"""Tests for CLI export/import commands."""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner

from env_vault.cli_export import export_group
from env_vault.storage import init_vault_dir, write_vault, get_meta_path
from env_vault.crypto import generate_key, save_key, encrypt


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_env(tmp_path):
    project = "myapp"
    key = generate_key()
    save_key(project, key, tmp_path)
    init_vault_dir(project, tmp_path)
    plaintext = b"SECRET=abc\nPORT=8080\n"
    encrypted = encrypt(plaintext, key)
    write_vault(project, encrypted, tmp_path)
    meta_path = get_meta_path(project, tmp_path)
    meta_path.write_text(json.dumps({"updated_at": "2024-06-01"}))
    return project, key, tmp_path


def test_export_cmd_creates_file(runner, vault_env, tmp_path):
    project, key, base = vault_env
    output = tmp_path / "out.json"
    result = runner.invoke(
        export_group,
        ["export", project, str(output), "--base-path", str(base)],
    )
    assert result.exit_code == 0
    assert output.exists()
    assert f"exported to {output}" in result.output


def test_export_cmd_fails_for_missing_vault(runner, tmp_path):
    result = runner.invoke(
        export_group,
        ["export", "ghost", str(tmp_path / "out.json"), "--base-path", str(tmp_path)],
    )
    assert result.exit_code == 1


def test_import_cmd_restores_vault(runner, vault_env, tmp_path):
    project, key, base = vault_env
    bundle = tmp_path / "bundle.json"
    runner.invoke(
        export_group,
        ["export", project, str(bundle), "--base-path", str(base)],
    )
    new_base = tmp_path / "new_home"
    new_base.mkdir()
    result = runner.invoke(
        export_group,
        ["import", str(bundle), "--base-path", str(new_base)],
    )
    assert result.exit_code == 0
    assert "imported successfully" in result.output


def test_import_cmd_fails_without_overwrite(runner, vault_env, tmp_path):
    project, key, base = vault_env
    bundle = tmp_path / "bundle.json"
    runner.invoke(
        export_group,
        ["export", project, str(bundle), "--base-path", str(base)],
    )
    result = runner.invoke(
        export_group,
        ["import", str(bundle), "--base-path", str(base)],
    )
    assert result.exit_code == 1
    assert "--overwrite" in result.output


def test_import_cmd_succeeds_with_overwrite(runner, vault_env, tmp_path):
    project, key, base = vault_env
    bundle = tmp_path / "bundle.json"
    runner.invoke(
        export_group,
        ["export", project, str(bundle), "--base-path", str(base)],
    )
    result = runner.invoke(
        export_group,
        ["import", str(bundle), "--base-path", str(base), "--overwrite"],
    )
    assert result.exit_code == 0


def test_plaintext_cmd_prints_env(runner, vault_env):
    project, key, base = vault_env
    result = runner.invoke(
        export_group,
        ["plaintext", project, "--base-path", str(base)],
    )
    assert result.exit_code == 0
    assert "SECRET=abc" in result.output
    assert "PORT=8080" in result.output
