"""Tests for env_vault.export module."""

import json
import pytest
from pathlib import Path

from env_vault.export import export_vault, import_vault, decrypt_to_plaintext
from env_vault.storage import init_vault_dir, write_vault, get_vault_path, get_meta_path
from env_vault.crypto import generate_key, save_key, encrypt


@pytest.fixture
def tmp_base(tmp_path):
    return tmp_path


@pytest.fixture
def populated_vault(tmp_base):
    project = "testproject"
    key = generate_key()
    save_key(project, key, tmp_base)
    init_vault_dir(project, tmp_base)

    plaintext = b"API_KEY=secret123\nDEBUG=true\n"
    encrypted = encrypt(plaintext, key)
    write_vault(project, encrypted, tmp_base)

    meta_path = get_meta_path(project, tmp_base)
    meta_path.write_text(json.dumps({"created_at": "2024-01-01"}))

    return project, key, tmp_base


def test_export_creates_bundle_file(populated_vault, tmp_path):
    project, key, base = populated_vault
    output = tmp_path / "vault_export.json"
    export_vault(project, output, base)
    assert output.exists()


def test_export_bundle_contains_expected_keys(populated_vault, tmp_path):
    project, key, base = populated_vault
    output = tmp_path / "vault_export.json"
    export_vault(project, output, base)
    bundle = json.loads(output.read_text())
    assert bundle["project"] == project
    assert "encrypted" in bundle
    assert "meta" in bundle
    assert bundle["version"] == 1


def test_export_raises_if_vault_missing(tmp_base, tmp_path):
    output = tmp_path / "out.json"
    with pytest.raises(FileNotFoundError):
        export_vault("nonexistent", output, tmp_base)


def test_import_restores_vault(populated_vault, tmp_path):
    project, key, base = populated_vault
    output = tmp_path / "bundle.json"
    export_vault(project, output, base)

    new_base = tmp_path / "new_home"
    new_base.mkdir()
    imported_project = import_vault(output, new_base)
    assert imported_project == project
    assert get_vault_path(project, new_base).exists()


def test_import_raises_if_bundle_missing(tmp_base):
    with pytest.raises(FileNotFoundError):
        import_vault(tmp_base / "missing.json", tmp_base)


def test_import_raises_if_vault_exists_no_overwrite(populated_vault, tmp_path):
    project, key, base = populated_vault
    output = tmp_path / "bundle.json"
    export_vault(project, output, base)
    with pytest.raises(FileExistsError):
        import_vault(output, base, overwrite=False)


def test_import_overwrites_when_flag_set(populated_vault, tmp_path):
    project, key, base = populated_vault
    output = tmp_path / "bundle.json"
    export_vault(project, output, base)
    imported = import_vault(output, base, overwrite=True)
    assert imported == project


def test_decrypt_to_plaintext_returns_env_string(populated_vault):
    project, key, base = populated_vault
    result = decrypt_to_plaintext(project, base)
    assert "API_KEY=secret123" in result
    assert "DEBUG=true" in result
