"""CLI commands for managing per-profile access control."""

from __future__ import annotations

import click

from env_vault.access import (
    can,
    get_permissions,
    list_actors,
    revoke_permissions,
    set_permissions,
)


@click.group("access")
def access_group() -> None:
    """Manage per-profile access permissions."""


@access_group.command("grant")
@click.argument("profile")
@click.argument("actor")
@click.option("--read/--no-read", default=True, show_default=True)
@click.option("--write/--no-write", default=True, show_default=True)
@click.pass_context
def grant_cmd(ctx: click.Context, profile: str, actor: str, read: bool, write: bool) -> None:
    """Grant permissions to ACTOR on PROFILE."""
    base = ctx.obj["base_path"]
    perms: list[str] = []
    if read:
        perms.append("read")
    if write:
        perms.append("write")
    if not perms:
        raise click.ClickException("At least one of --read or --write must be set.")
    set_permissions(base, profile, actor, perms)
    click.echo(f"Granted {', '.join(perms)} to '{actor}' on profile '{profile}'.")


@access_group.command("revoke")
@click.argument("profile")
@click.argument("actor")
@click.pass_context
def revoke_cmd(ctx: click.Context, profile: str, actor: str) -> None:
    """Revoke all explicit permissions for ACTOR on PROFILE."""
    base = ctx.obj["base_path"]
    removed = revoke_permissions(base, profile, actor)
    if removed:
        click.echo(f"Revoked permissions for '{actor}' on profile '{profile}'.")
    else:
        click.echo(f"No explicit permissions found for '{actor}' on profile '{profile}'.")


@access_group.command("show")
@click.argument("profile")
@click.pass_context
def show_cmd(ctx: click.Context, profile: str) -> None:
    """Show all actors with explicit permissions on PROFILE."""
    base = ctx.obj["base_path"]
    actors = list_actors(base, profile)
    if not actors:
        click.echo(f"No explicit access rules for profile '{profile}' (all actors have full access).")
        return
    for actor, perms in sorted(actors.items()):
        click.echo(f"  {actor}: {', '.join(perms)}")


@access_group.command("check")
@click.argument("profile")
@click.argument("actor")
@click.argument("permission", type=click.Choice(["read", "write"]))
@click.pass_context
def check_cmd(ctx: click.Context, profile: str, actor: str, permission: str) -> None:
    """Check if ACTOR has PERMISSION on PROFILE."""
    base = ctx.obj["base_path"]
    allowed = can(base, profile, actor, permission)
    status = "allowed" if allowed else "denied"
    click.echo(f"'{actor}' {permission} on '{profile}': {status}")
    ctx.exit(0 if allowed else 1)
