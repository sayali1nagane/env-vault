"""Main CLI entry-point for env-vault."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.crypto import generate_key, save_key, load_key, encrypt, decrypt
from env_vault.storage import (
    get_vault_dir,
    get_vault_path,
    get_meta_path,
    init_vault_dir,
    write_vault,
    read_vault,
)
from env_vault.parser import parse_env_string, serialize_env_dict, diff_env_dicts
from env_vault.cli_export import export_group
from env_vault.cli_audit import audit_group
from env_vault.cli_rotate import rotate_group
from env_vault.cli_profile import profile_group
from env_vault.cli_snapshot import snapshot_group
from env_vault.cli_tags import tags_group
from env_vault.cli_compare import compare_group
from env_vault.cli_lint import lint_group
from env_vault.cli_template import template_group
from env_vault.cli_history import history_group
from env_vault.cli_remind import remind_group


@click.group()
def cli() -> None:
    """env-vault: encrypted .env file manager."""


cli.add_command(export_group, "export")
cli.add_command(audit_group, "audit")
cli.add_command(rotate_group, "rotate")
cli.add_command(profile_group, "profile")
cli.add_command(snapshot_group, "snapshot")
cli.add_command(tags_group, "tags")
cli.add_command(compare_group, "compare")
cli.add_command(lint_group, "lint")
cli.add_command(template_group, "template")
cli.add_command(history_group, "history")
cli.add_command(remind_group, "remind")


@cli.command("init")
@click.option("--base-path", default=".", show_default=True)
def init(base_path: str) -> None:
    """Initialise a new vault in the current project."""
    base = Path(base_path)
    vault_dir = get_vault_dir(base)
    if vault_dir.exists():
        raise click.ClickException("Vault already initialised.")
    init_vault_dir(base)
    key = generate_key()
    save_key(key, base)
    click.echo(f"Vault initialised at {vault_dir}")


@cli.command("set")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--base-path", default=".", show_default=True)
@click.option("--profile", default="default", show_default=True)
def set_cmd(env_file: str, base_path: str, profile: str) -> None:
    """Encrypt and store an .env file in the vault."""
    base = Path(base_path)
    key = load_key(base)
    plaintext = Path(env_file).read_bytes()
    ciphertext = encrypt(key, plaintext)
    write_vault(ciphertext, base, profile)
    click.echo(f"Encrypted '{env_file}' into profile '{profile}'.")


@cli.command("get")
@click.argument("key_name")
@click.option("--base-path", default=".", show_default=True)
@click.option("--profile", default="default", show_default=True)
def get_cmd(key_name: str, base_path: str, profile: str) -> None:
    """Retrieve a single value from the vault."""
    base = Path(base_path)
    key = load_key(base)
    ciphertext = read_vault(base, profile)
    plaintext = decrypt(key, ciphertext).decode()
    env = parse_env_string(plaintext)
    if key_name not in env:
        raise click.ClickException(f"Key '{key_name}' not found in profile '{profile}'.")
    click.echo(env[key_name])


@cli.command("diff")
@click.argument("env_file", type=click.Path(exists=True))
@click.option("--base-path", default=".", show_default=True)
@click.option("--profile", default="default", show_default=True)
def diff(env_file: str, base_path: str, profile: str) -> None:
    """Show diff between a local .env file and the stored vault."""
    base = Path(base_path)
    key = load_key(base)
    ciphertext = read_vault(base, profile)
    stored = parse_env_string(decrypt(key, ciphertext).decode())
    local = parse_env_string(Path(env_file).read_text())
    changes = diff_env_dicts(stored, local)
    if not changes:
        click.echo("No differences found.")
        return
    for change in changes:
        click.echo(change)
