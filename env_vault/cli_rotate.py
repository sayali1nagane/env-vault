"""CLI commands for key rotation in env-vault."""

import click
from pathlib import Path

from .rotate import rotate_key, get_rotation_info


@click.group("rotate")
def rotate_group():
    """Key rotation commands."""


@rotate_group.command("run")
@click.argument("project")
@click.option(
    "--base-path",
    default=".",
    show_default=True,
    help="Base directory where .env-vault is stored.",
)
@click.confirmation_option(
    prompt="Rotating the key will re-encrypt the vault. Continue?"
)
def rotate_cmd(project: str, base_path: str):
    """Rotate the encryption key for PROJECT."""
    base = Path(base_path)
    try:
        new_key = rotate_key(project, base)
        click.echo(
            click.style(f"Key rotated successfully for '{project}'.", fg="green")
        )
        click.echo(f"New key (hex): {new_key.hex()[:16]}...")
    except FileNotFoundError as exc:
        click.echo(click.style(str(exc), fg="red"), err=True)
        raise SystemExit(1)
    except Exception as exc:
        click.echo(
            click.style(f"Rotation failed: {exc}", fg="red"), err=True
        )
        raise SystemExit(1)


@rotate_group.command("info")
@click.argument("project")
@click.option(
    "--base-path",
    default=".",
    show_default=True,
    help="Base directory where .env-vault is stored.",
)
def info_cmd(project: str, base_path: str):
    """Show last key rotation info for PROJECT."""
    base = Path(base_path)
    info = get_rotation_info(project, base)
    last = info.get("last_rotated")
    if last:
        click.echo(f"Last rotated: {last}")
    else:
        click.echo("No rotation recorded for this project.")
