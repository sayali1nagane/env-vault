"""Command-line interface for env-vault."""

import sys
import click
from pathlib import Path

from env_vault.crypto import generate_key, save_key, load_key, encrypt, decrypt
from env_vault.storage import (
    get_vault_dir,
    init_vault_dir,
    write_vault,
    read_vault,
    write_meta,
    read_meta,
)
from env_vault.parser import parse_env_string, serialize_env_dict, diff_env_dicts


@click.group()
def cli():
    """env-vault: encrypt and manage project-level .env files."""
    pass


@cli.command()
@click.option("--base", default=".", help="Base directory for the vault.", show_default=True)
def init(base):
    """Initialize a new env-vault in the current project."""
    base_path = Path(base).resolve()
    vault_dir = get_vault_dir(base_path)

    if vault_dir.exists():
        click.echo(f"Vault already initialized at {vault_dir}")
        sys.exit(1)

    init_vault_dir(base_path)
    key = generate_key()
    save_key(key, base_path)
    write_meta({"version": 1, "entries": []}, base_path)
    click.echo(f"Vault initialized at {vault_dir}")
    click.echo("Key saved locally. Do NOT commit the .env-vault/key file.")


@cli.command(name="set")
@click.argument("env_file", default=".env")
@click.option("--base", default=".", help="Base directory for the vault.", show_default=True)
def set_cmd(env_file, base):
    """Encrypt and store an .env file into the vault."""
    base_path = Path(base).resolve()
    env_path = Path(env_file).resolve()

    if not env_path.exists():
        click.echo(f"File not found: {env_path}")
        sys.exit(1)

    key = load_key(base_path)
    plaintext = env_path.read_bytes()
    ciphertext = encrypt(key, plaintext)
    write_vault(ciphertext, base_path)

    meta = read_meta(base_path) or {"version": 1, "entries": []}
    if str(env_path) not in meta["entries"]:
        meta["entries"].append(str(env_path))
    write_meta(meta, base_path)

    click.echo(f"Encrypted {env_path} -> vault")


@cli.command(name="get")
@click.argument("output_file", default=".env")
@click.option("--base", default=".", help="Base directory for the vault.", show_default=True)
def get_cmd(output_file, base):
    """Decrypt and restore the .env file from the vault."""
    base_path = Path(base).resolve()
    output_path = Path(output_file).resolve()

    key = load_key(base_path)
    ciphertext = read_vault(base_path)
    plaintext = decrypt(key, ciphertext)
    output_path.write_bytes(plaintext)
    click.echo(f"Decrypted vault -> {output_path}")


@cli.command()
@click.argument("env_file", default=".env")
@click.option("--base", default=".", help="Base directory for the vault.", show_default=True)
def diff(env_file, base):
    """Show diff between local .env and the encrypted vault contents."""
    base_path = Path(base).resolve()
    env_path = Path(env_file).resolve()

    if not env_path.exists():
        click.echo(f"File not found: {env_path}")
        sys.exit(1)

    key = load_key(base_path)
    ciphertext = read_vault(base_path)
    vault_plaintext = decrypt(key, ciphertext).decode()
    local_plaintext = env_path.read_text()

    vault_env = parse_env_string(vault_plaintext)
    local_env = parse_env_string(local_plaintext)
    added, removed, changed = diff_env_dicts(vault_env, local_env)

    if not added and not removed and not changed:
        click.echo("No differences found.")
        return

    for key_name in added:
        click.echo(click.style(f"+ {key_name}={local_env[key_name]}", fg="green"))
    for key_name in removed:
        click.echo(click.style(f"- {key_name}={vault_env[key_name]}", fg="red"))
    for key_name in changed:
        click.echo(click.style(f"~ {key_name}: {vault_env[key_name]} -> {local_env[key_name]}", fg="yellow"))


if __name__ == "__main__":
    cli()
