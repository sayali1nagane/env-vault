"""CLI commands for audit log inspection."""

import click
from pathlib import Path

from env_vault.audit import read_audit_log, format_audit_log


@click.group("audit")
def audit_group():
    """Commands for inspecting the vault audit log."""


@audit_group.command("log")
@click.option(
    "--base",
    default=".",
    show_default=True,
    help="Base directory containing the .env-vault folder.",
)
@click.option(
    "--last",
    default=0,
    type=int,
    show_default=True,
    help="Show only the last N entries (0 = all).",
)
@click.option(
    "--action",
    default=None,
    help="Filter entries by action name.",
)
def log_cmd(base: str, last: int, action: str):
    """Display the vault audit log."""
    base_path = Path(base).resolve()
    entries = read_audit_log(base_path)

    if not entries:
        click.echo("No audit log entries found.")
        return

    if action:
        entries = [e for e in entries if e.get("action") == action]
        if not entries:
            click.echo(f"No entries found for action: {action}")
            return

    if last > 0:
        entries = entries[-last:]

    click.echo(format_audit_log(entries))


@audit_group.command("clear")
@click.option(
    "--base",
    default=".",
    show_default=True,
    help="Base directory containing the .env-vault folder.",
)
@click.confirmation_option(prompt="Are you sure you want to clear the audit log?")
def clear_cmd(base: str):
    """Clear the vault audit log."""
    from env_vault.audit import get_audit_path
    base_path = Path(base).resolve()
    audit_path = get_audit_path(base_path)
    if audit_path.exists():
        audit_path.write_text("")
        click.echo("Audit log cleared.")
    else:
        click.echo("No audit log found.")
