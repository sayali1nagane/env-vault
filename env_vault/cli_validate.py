"""CLI commands for validating env vault contents."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .crypto import load_key
from .export import decrypt_to_plaintext
from .parser import parse_env_string
from .storage import get_vault_path
from .validate import validate_env


@click.group("validate")
def validate_group() -> None:
    """Validate env variable values against rules."""


@validate_group.command("check")
@click.option("--profile", default="default", show_default=True, help="Profile to validate.")
@click.option(
    "--rules",
    "rules_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="JSON file mapping key names to rule identifiers.",
)
@click.option(
    "--require",
    "required_keys",
    multiple=True,
    help="Keys that must be present. Repeatable.",
)
@click.option("--base", default=".", show_default=True, help="Base directory of the vault.")
@click.pass_context
def check_cmd(
    ctx: click.Context,
    profile: str,
    rules_file: str,
    required_keys: tuple,
    base: str,
) -> None:
    """Run validation rules against a vault profile."""
    base_path = Path(base)
    vault_path = get_vault_path(base_path, profile)
    if not vault_path.exists():
        click.echo(f"No vault found for profile '{profile}'.", err=True)
        ctx.exit(1)

    rules: dict = json.loads(Path(rules_file).read_text())

    key = load_key(base_path, profile)
    plaintext = decrypt_to_plaintext(base_path, key, profile)
    env = parse_env_string(plaintext)

    result = validate_env(env, rules, list(required_keys) or None)

    if not result.issues:
        click.echo(click.style("All checks passed.", fg="green"))
        return

    for issue in result.issues:
        colour = "red" if issue.severity == "error" else "yellow"
        click.echo(click.style(str(issue), fg=colour))

    if not result.ok():
        sys.exit(1)
