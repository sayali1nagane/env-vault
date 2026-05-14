"""CLI commands for vault tag management."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.tags import add_tag, get_tags, list_profiles_by_tag, remove_tag


@click.group(name="tags")
def tags_group() -> None:
    """Manage tags attached to vault profiles."""


@tags_group.command(name="add")
@click.argument("tag")
@click.option("--profile", default="default", show_default=True, help="Vault profile name.")
@click.option("--base", default=".", show_default=True, help="Base project directory.")
def add_cmd(tag: str, profile: str, base: str) -> None:
    """Add TAG to the specified vault profile."""
    base_path = Path(base).resolve()
    try:
        updated = add_tag(base_path, tag, profile)
        click.echo(f"Tags for '{profile}': {', '.join(updated)}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


@tags_group.command(name="remove")
@click.argument("tag")
@click.option("--profile", default="default", show_default=True, help="Vault profile name.")
@click.option("--base", default=".", show_default=True, help="Base project directory.")
def remove_cmd(tag: str, profile: str, base: str) -> None:
    """Remove TAG from the specified vault profile."""
    base_path = Path(base).resolve()
    try:
        updated = remove_tag(base_path, tag, profile)
        remaining = ", ".join(updated) if updated else "(none)"
        click.echo(f"Tags for '{profile}': {remaining}")
    except KeyError as exc:
        raise click.ClickException(str(exc))


@tags_group.command(name="list")
@click.option("--profile", default="default", show_default=True, help="Vault profile name.")
@click.option("--base", default=".", show_default=True, help="Base project directory.")
def list_cmd(profile: str, base: str) -> None:
    """List all tags for a vault profile."""
    base_path = Path(base).resolve()
    tags = get_tags(base_path, profile)
    if tags:
        for t in tags:
            click.echo(t)
    else:
        click.echo("No tags set.")


@tags_group.command(name="find")
@click.argument("tag")
@click.option("--base", default=".", show_default=True, help="Base project directory.")
def find_cmd(tag: str, base: str) -> None:
    """Find all profiles that carry TAG."""
    base_path = Path(base).resolve()
    profiles = list_profiles_by_tag(base_path, tag)
    if profiles:
        for p in profiles:
            click.echo(p)
    else:
        click.echo(f"No profiles found with tag '{tag}'.")
