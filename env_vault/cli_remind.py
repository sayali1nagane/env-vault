"""CLI commands for rotation reminder configuration."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.remind import check_rotation_due, get_reminder_config, set_reminder_config


@click.group("remind")
def remind_group() -> None:
    """Manage key-rotation reminders."""


@remind_group.command("status")
@click.option("--base-path", default=".", show_default=True, help="Project base path.")
@click.option("--profile", default="default", show_default=True)
def status_cmd(base_path: str, profile: str) -> None:
    """Show whether a key rotation is due for a profile."""
    base = Path(base_path)
    config = get_reminder_config(base)
    if not config.get("enabled", True):
        click.echo("Rotation reminders are disabled.")
        return

    overdue = check_rotation_due(base, profile)
    interval = config["interval_days"]
    if overdue is None:
        click.echo(f"Profile '{profile}': rotation not due (interval: {interval} days).")
    else:
        click.secho(
            f"Profile '{profile}': rotation OVERDUE by {overdue} day(s) "
            f"(interval: {interval} days).",
            fg="yellow",
        )


@remind_group.command("configure")
@click.option("--base-path", default=".", show_default=True)
@click.option("--interval", required=True, type=int, help="Rotation interval in days.")
@click.option("--disable", is_flag=True, default=False, help="Disable reminders.")
def configure_cmd(base_path: str, interval: int, disable: bool) -> None:
    """Set the rotation reminder interval (and optionally disable it)."""
    base = Path(base_path)
    try:
        config = set_reminder_config(base, interval_days=interval, enabled=not disable)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    state = "disabled" if not config["enabled"] else "enabled"
    click.echo(f"Reminder {state}: interval set to {config['interval_days']} day(s).")
