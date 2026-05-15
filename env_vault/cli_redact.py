"""CLI commands for redacted display of vault contents."""

from __future__ import annotations

import click

from .crypto import load_key
from .parser import parse_env_string
from .redact import redact_env_dict, format_redacted_table
from .storage import get_vault_path, get_meta_path, read_vault


@click.group(name="redact")
def redact_group() -> None:
    """Commands for safely displaying vault contents with sensitive values masked."""


@redact_group.command(name="show")
@click.option("--profile", default="default", show_default=True, help="Vault profile to display.")
@click.option("--all", "redact_all", is_flag=True, default=False, help="Redact every value.")
@click.option("--extra", multiple=True, metavar="KEY", help="Additional keys to redact (repeatable).")
@click.pass_context
def show_cmd(ctx: click.Context, profile: str, redact_all: bool, extra: tuple) -> None:
    """Display vault variables with sensitive values masked."""
    base = ctx.obj.get("base_path", ".")
    vault_path = get_vault_path(base, profile)
    if not vault_path.exists():
        raise click.ClickException(f"No vault found for profile '{profile}'. Run 'init' first.")

    key = load_key(base)
    raw = read_vault(base, profile, key)
    env = parse_env_string(raw)
    redacted = redact_env_dict(env, extra_keys=list(extra), redact_all=redact_all)
    click.echo(format_redacted_table(redacted))


@redact_group.command(name="check")
@click.option("--profile", default="default", show_default=True, help="Vault profile to inspect.")
@click.pass_context
def check_cmd(ctx: click.Context, profile: str) -> None:
    """List which keys would be redacted in the given profile."""
    base = ctx.obj.get("base_path", ".")
    vault_path = get_vault_path(base, profile)
    if not vault_path.exists():
        raise click.ClickException(f"No vault found for profile '{profile}'.")

    key = load_key(base)
    raw = read_vault(base, profile, key)
    env = parse_env_string(raw)

    sensitive = [k for k in env if _key_is_sensitive(k)]
    if not sensitive:
        click.echo("No sensitive keys detected.")
    else:
        click.echo(f"Sensitive keys ({len(sensitive)}):")
        for k in sorted(sensitive):
            click.echo(f"  {k}")


def _key_is_sensitive(key: str) -> bool:
    from .redact import is_sensitive_key
    return is_sensitive_key(key)
