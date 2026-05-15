"""CLI commands for pin management."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.pin import list_pins, set_pin, remove_pin, get_pin


@click.group(name="pin")
def pin_group():
    """Manage pinned env key values."""


@pin_group.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--base", default=".", help="Base path for the vault.")
def set_cmd(key: str, value: str, base: str):
    """Pin KEY to VALUE across all profiles."""
    try:
        set_pin(Path(base), key, value)
        click.echo(f"Pinned {key.upper()} = {value}")
    except ValueError as exc:
        raise click.ClickException(str(exc))


@pin_group.command(name="get")
@click.argument("key")
@click.option("--base", default=".", help="Base path for the vault.")
def get_cmd(key: str, base: str):
    """Show the pinned value for KEY."""
    value = get_pin(Path(base), key)
    if value is None:
        click.echo(f"{key.upper()} is not pinned.")
    else:
        click.echo(f"{key.upper()} = {value}")


@pin_group.command(name="remove")
@click.argument("key")
@click.option("--base", default=".", help="Base path for the vault.")
def remove_cmd(key: str, base: str):
    """Remove a pinned KEY."""
    removed = remove_pin(Path(base), key)
    if removed:
        click.echo(f"Removed pin for {key.upper()}.")
    else:
        click.echo(f"No pin found for {key.upper()}.")


@pin_group.command(name="list")
@click.option("--base", default=".", help="Base path for the vault.")
def list_cmd(base: str):
    """List all pinned keys and their values."""
    pins = list_pins(Path(base))
    if not pins:
        click.echo("No pins configured.")
        return
    for key, value in sorted(pins.items()):
        click.echo(f"{key} = {value}")
