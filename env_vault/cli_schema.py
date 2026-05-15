"""CLI commands for managing and enforcing .env schemas."""
from __future__ import annotations

import json
from pathlib import Path

import click

from env_vault.schema import (
    delete_schema,
    load_schema,
    save_schema,
    validate_against_schema,
)
from env_vault.storage import load_vault, get_vault_path
from env_vault.crypto import load_key
from env_vault.parser import parse_env_string


@click.group(name="schema")
def schema_group() -> None:
    """Manage key schemas for env profiles."""


@schema_group.command("set")
@click.argument("key")
@click.option("--required/--optional", default=False, help="Mark key as required.")
@click.option("--type", "key_type", default=None, type=click.Choice(["url", "int"]), help="Expected value type.")
@click.option("--allowed", default=None, help="Comma-separated list of allowed values.")
@click.option("--profile", default="default", show_default=True)
@click.pass_context
def set_cmd(ctx: click.Context, key: str, required: bool, key_type: str | None, allowed: str | None, profile: str) -> None:
    """Add or update a schema rule for KEY."""
    base = Path(ctx.obj.get("base_path", "."))
    schema = load_schema(base, profile)
    rule: dict = {"required": required}
    if key_type:
        rule["type"] = key_type
    if allowed:
        rule["allowed"] = [v.strip() for v in allowed.split(",")]
    schema[key.upper()] = rule
    save_schema(base, schema, profile)
    click.echo(f"Schema rule saved for {key.upper()} in profile '{profile}'.")


@schema_group.command("show")
@click.option("--profile", default="default", show_default=True)
@click.pass_context
def show_cmd(ctx: click.Context, profile: str) -> None:
    """Display the current schema for a profile."""
    base = Path(ctx.obj.get("base_path", "."))
    schema = load_schema(base, profile)
    if not schema:
        click.echo(f"No schema defined for profile '{profile}'.")
        return
    click.echo(json.dumps(schema, indent=2))


@schema_group.command("check")
@click.option("--profile", default="default", show_default=True)
@click.pass_context
def check_cmd(ctx: click.Context, profile: str) -> None:
    """Validate the current vault contents against the schema."""
    base = Path(ctx.obj.get("base_path", "."))
    schema = load_schema(base, profile)
    if not schema:
        click.echo(f"No schema defined for profile '{profile}'. Nothing to check.")
        return
    vault_path = get_vault_path(base, profile)
    if not vault_path.exists():
        click.echo(f"Vault for profile '{profile}' not found.", err=True)
        ctx.exit(1)
        return
    key = load_key(base, profile)
    ciphertext = vault_path.read_bytes()
    from env_vault.crypto import decrypt
    plaintext = decrypt(ciphertext, key)
    env = parse_env_string(plaintext.decode())
    violations = validate_against_schema(env, schema)
    if not violations:
        click.echo(f"✓ Profile '{profile}' passes all schema checks.")
    else:
        click.echo(f"Schema violations in profile '{profile}':")
        for v in violations:
            click.echo(f"  ✗ {v}")
        ctx.exit(1)


@schema_group.command("delete")
@click.option("--profile", default="default", show_default=True)
@click.pass_context
def delete_cmd(ctx: click.Context, profile: str) -> None:
    """Remove the schema for a profile."""
    base = Path(ctx.obj.get("base_path", "."))
    removed = delete_schema(base, profile)
    if removed:
        click.echo(f"Schema for profile '{profile}' deleted.")
    else:
        click.echo(f"No schema found for profile '{profile}'.")
