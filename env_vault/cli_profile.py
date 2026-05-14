"""CLI commands for managing named environment profiles."""

import click
from pathlib import Path

from env_vault.profile import (
    list_profiles,
    get_active_profile,
    set_active_profile,
    copy_profile,
    delete_profile,
)
from env_vault.storage import get_vault_dir, load_key
from env_vault.crypto import load_key as crypto_load_key


@click.group(name="profile")
def profile_group():
    """Manage named environment profiles."""


@profile_group.command(name="list")
@click.option("--base", default=".", help="Base project path.")
def list_cmd(base: str):
    """List all available profiles."""
    base_path = Path(base)
    profiles = list_profiles(base_path)
    active = get_active_profile(base_path)
    if not profiles:
        click.echo("No profiles found. Run 'env-vault init' first.")
        return
    for p in profiles:
        marker = " (active)" if p == active else ""
        click.echo(f"  {p}{marker}")


@profile_group.command(name="use")
@click.argument("profile")
@click.option("--base", default=".", help="Base project path.")
def use_cmd(profile: str, base: str):
    """Switch the active profile."""
    base_path = Path(base)
    profiles = list_profiles(base_path)
    if profile not in profiles:
        click.echo(f"Error: Profile '{profile}' does not exist.", err=True)
        raise SystemExit(1)
    set_active_profile(base_path, profile)
    click.echo(f"Switched to profile '{profile}'.")


@profile_group.command(name="copy")
@click.argument("src")
@click.argument("dst")
@click.option("--base", default=".", help="Base project path.")
def copy_cmd(src: str, dst: str, base: str):
    """Copy a profile to a new profile name."""
    base_path = Path(base)
    try:
        key = crypto_load_key(base_path)
        copy_profile(base_path, src, dst, key)
        click.echo(f"Profile '{src}' copied to '{dst}'.")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@profile_group.command(name="delete")
@click.argument("profile")
@click.option("--base", default=".", help="Base project path.")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def delete_cmd(profile: str, base: str):
    """Delete a profile."""
    base_path = Path(base)
    try:
        delete_profile(base_path, profile)
        click.echo(f"Profile '{profile}' deleted.")
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
