"""CLI commands for syncing a .env file with the vault."""
from __future__ import annotations

from pathlib import Path

import click

from env_vault.sync import diff_against_file, sync_from_file


@click.group("sync")
def sync_group() -> None:
    """Sync vault with a plaintext .env file."""


@sync_group.command("diff")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--profile", default="default", show_default=True, help="Vault profile.")
@click.option("--base", default=".vault", show_default=True, help="Vault base directory.")
def diff_cmd(env_file: Path, profile: str, base: str) -> None:
    """Show differences between ENV_FILE and the encrypted vault."""
    base_path = Path(base)
    result = diff_against_file(env_file, base_path, profile)
    if not result.has_changes:
        click.echo("Vault is up-to-date with the file.")
        return
    click.echo(f"Changes detected in profile '{profile}':")
    click.echo(result.summary())


@sync_group.command("apply")
@click.argument("env_file", type=click.Path(exists=True, path_type=Path))
@click.option("--profile", default="default", show_default=True, help="Vault profile.")
@click.option("--base", default=".vault", show_default=True, help="Vault base directory.")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def apply_cmd(env_file: Path, profile: str, base: str, yes: bool) -> None:
    """Apply changes from ENV_FILE into the encrypted vault."""
    base_path = Path(base)
    result = diff_against_file(env_file, base_path, profile)
    if not result.has_changes:
        click.echo("Nothing to sync — vault already matches the file.")
        return

    click.echo(f"Pending changes for profile '{profile}':")
    click.echo(result.summary())

    if not yes:
        click.confirm("Apply these changes to the vault?", abort=True)

    sync_from_file(env_file, base_path, profile)
    click.echo("Vault updated successfully.")
