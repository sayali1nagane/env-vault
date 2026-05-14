"""CLI commands for linting vault env contents."""

from __future__ import annotations

import click

from .crypto import load_key
from .storage import get_vault_path, read_vault
from .crypto import decrypt
from .lint import lint_env_string


@click.group(name="lint")
def lint_group() -> None:
    """Lint and validate .env file contents."""


@lint_group.command(name="check")
@click.option("--profile", default="default", show_default=True, help="Profile to lint.")
@click.option("--strict", is_flag=True, default=False, help="Exit non-zero on warnings too.")
@click.pass_context
def check_cmd(ctx: click.Context, profile: str, strict: bool) -> None:
    """Decrypt and lint the specified profile's .env contents."""
    base = ctx.obj.get("base_path", ".")

    vault_path = get_vault_path(base, profile)
    if not vault_path.exists():
        click.echo(f"No vault found for profile '{profile}'.", err=True)
        ctx.exit(1)
        return

    try:
        key = load_key(base, profile)
    except FileNotFoundError:
        click.echo("Encryption key not found.", err=True)
        ctx.exit(1)
        return

    ciphertext = read_vault(base, profile)
    plaintext = decrypt(ciphertext, key)

    result = lint_env_string(plaintext)

    if not result.issues:
        click.echo(click.style("No issues found.", fg="green"))
        return

    for issue in result.issues:
        colour = {"error": "red", "warning": "yellow", "info": "cyan"}.get(
            issue.severity, "white"
        )
        click.echo(click.style(str(issue), fg=colour))

    click.echo(f"\n{result.summary()}")

    if result.has_errors or (strict and result.has_warnings):
        ctx.exit(1)
