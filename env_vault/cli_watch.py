"""CLI commands for watching .env file changes."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.watch import (
    check_for_changes,
    clear_watch_state,
    load_watch_state,
    record_watch_state,
)


@click.group(name="watch")
def watch_group() -> None:
    """Track external changes to .env files."""


@watch_group.command(name="record")
@click.argument("env_file", default=".env")
@click.pass_context
def record_cmd(ctx: click.Context, env_file: str) -> None:
    """Record the current state of ENV_FILE as a baseline."""
    base_path = Path(ctx.obj.get("base_path", "."))
    env_path = Path(env_file)

    if not env_path.exists():
        raise click.ClickException(f"File not found: {env_file}")

    state = record_watch_state(env_path, base_path)
    click.echo(f"Recorded state for {env_file}")
    click.echo(f"  hash: {state['hash'][:12]}...")


@watch_group.command(name="check")
@click.argument("env_file", default=".env")
@click.pass_context
def check_cmd(ctx: click.Context, env_file: str) -> None:
    """Check if ENV_FILE has changed since last recorded state."""
    base_path = Path(ctx.obj.get("base_path", "."))
    env_path = Path(env_file)

    result = check_for_changes(env_path, base_path)

    if result["changed"]:
        click.echo(click.style(f"CHANGED: {result['reason']}", fg="yellow"))
        click.echo(f"  previous: {result['previous_hash']}")
        click.echo(f"  current:  {result['current_hash']}")
        ctx.exit(1)
    else:
        click.echo(click.style("No changes detected.", fg="green"))


@watch_group.command(name="status")
@click.pass_context
def status_cmd(ctx: click.Context) -> None:
    """Show the current watch state metadata."""
    base_path = Path(ctx.obj.get("base_path", "."))
    state = load_watch_state(base_path)

    if state is None:
        click.echo("No watch state recorded. Run `watch record` first.")
        return

    click.echo(f"Watching: {state['path']}")
    click.echo(f"  hash:        {state['hash']}")
    click.echo(f"  recorded at: {state['recorded_at']}")


@watch_group.command(name="clear")
@click.pass_context
def clear_cmd(ctx: click.Context) -> None:
    """Clear the stored watch state."""
    base_path = Path(ctx.obj.get("base_path", "."))
    clear_watch_state(base_path)
    click.echo("Watch state cleared.")
