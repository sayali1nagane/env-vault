"""CLI commands for env-vault template management."""

from __future__ import annotations

from pathlib import Path

import click

from .template import (
    list_templates,
    save_template,
    load_template,
    delete_template,
    apply_template,
)
from .storage import get_vault_path, read_vault, write_vault
from .crypto import load_key
from .parser import parse_env_string


@click.group("template")
def template_group() -> None:
    """Manage .env templates (key skeletons)."""


@template_group.command("save")
@click.argument("name")
@click.argument("keys", nargs=-1, required=True)
@click.option("--base", default=".", show_default=True, help="Vault base directory.")
def save_cmd(name: str, keys: tuple, base: str) -> None:
    """Save a template with the given KEY names."""
    path = save_template(Path(base), name, list(keys))
    click.echo(f"Template '{name}' saved with {len(keys)} key(s) → {path}")


@template_group.command("list")
@click.option("--base", default=".", show_default=True)
def list_cmd(base: str) -> None:
    """List all saved templates."""
    templates = list_templates(Path(base))
    if not templates:
        click.echo("No templates found.")
    else:
        for t in templates:
            click.echo(f"  {t}")


@template_group.command("show")
@click.argument("name")
@click.option("--base", default=".", show_default=True)
def show_cmd(name: str, base: str) -> None:
    """Show the keys defined in a template."""
    try:
        keys = load_template(Path(base), name)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Template '{name}' keys:")
    for k in keys:
        click.echo(f"  {k}")


@template_group.command("delete")
@click.argument("name")
@click.option("--base", default=".", show_default=True)
@click.confirmation_option(prompt="Delete this template?")
def delete_cmd(name: str, base: str) -> None:
    """Delete a saved template."""
    try:
        delete_template(Path(base), name)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Template '{name}' deleted.")


@template_group.command("apply")
@click.argument("name")
@click.option("--profile", default="default", show_default=True)
@click.option("--base", default=".", show_default=True)
def apply_cmd(name: str, profile: str, base: str) -> None:
    """Apply a template to a profile, adding any missing keys (empty values)."""
    base_path = Path(base)
    key = load_key(base_path, profile)
    raw = read_vault(base_path, profile, key)
    env = parse_env_string(raw)
    try:
        merged = apply_template(base_path, name, env)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc))
    added = [k for k in merged if k not in env]
    from .parser import serialize_env_dict
    write_vault(base_path, profile, key, serialize_env_dict(merged))
    if added:
        click.echo(f"Added {len(added)} missing key(s): {', '.join(added)}")
    else:
        click.echo("Profile already contains all template keys. Nothing changed.")
