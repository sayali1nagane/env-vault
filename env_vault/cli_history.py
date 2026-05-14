"""CLI commands for browsing per-key change history."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.history import (
    clear_key_history,
    get_key_history,
    list_tracked_keys,
)


@click.group("history")
def history_group() -> None:
    """View and manage per-key change history."""


@history_group.command("log")
@click.argument("key")
@click.option("--profile", default="default", show_default=True)
@click.pass_context
def log_cmd(ctx: click.Context, key: str, profile: str) -> None:
    """Show change history for KEY."""
    base_path = Path(ctx.obj["base_path"])
    entries = get_key_history(base_path, key, profile)
    if not entries:
        click.echo(f"No history found for '{key}'.")
        return
    for entry in entries:
        old = entry["old"] if entry["old"] is not None else "(unset)"
        new = entry["new"] if entry["new"] is not None else "(deleted)"
        click.echo(f"[{entry['timestamp']}] {old} → {new}  (by {entry['actor']})")


@history_group.command("keys")
@click.option("--profile", default="default", show_default=True)
@click.pass_context
def keys_cmd(ctx: click.Context, profile: str) -> None:
    """List all keys that have recorded history."""
    base_path = Path(ctx.obj["base_path"])
    keys = list_tracked_keys(base_path, profile)
    if not keys:
        click.echo("No history recorded yet.")
        return
    for k in keys:
        click.echo(k)


@history_group.command("clear")
@click.argument("key")
@click.option("--profile", default="default", show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def clear_cmd(ctx: click.Context, key: str, profile: str, yes: bool) -> None:
    """Delete all history entries for KEY."""
    base_path = Path(ctx.obj["base_path"])
    if not yes:
        click.confirm(f"Clear all history for '{key}'?", abort=True)
    clear_key_history(base_path, key, profile)
    click.echo(f"History cleared for '{key}'.")
