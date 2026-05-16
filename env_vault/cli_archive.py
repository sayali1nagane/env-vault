"""CLI commands for vault archive management."""

from __future__ import annotations

from pathlib import Path

import click

from env_vault.archive import create_archive, restore_archive, list_archives, delete_archive


@click.group("archive")
def archive_group() -> None:
    """Archive and restore vault profiles."""


@archive_group.command("save")
@click.argument("profile", default="default")
@click.option("--name", default=None, help="Custom archive name (default: auto-generated)")
@click.option("--base", default=".", help="Base project path")
def save_cmd(profile: str, name: str | None, base: str) -> None:
    """Create a compressed archive of a vault profile."""
    base_path = Path(base).resolve()
    try:
        dest = create_archive(base_path, profile, name)
        click.echo(f"Archived profile '{profile}' → {dest.name}")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@archive_group.command("restore")
@click.argument("archive_name")
@click.option("--profile", default=None, help="Override restored profile name")
@click.option("--base", default=".", help="Base project path")
def restore_cmd(archive_name: str, profile: str | None, base: str) -> None:
    """Restore a vault profile from an archive."""
    base_path = Path(base).resolve()
    archives_dir = base_path / ".env-vault" / "archives"
    archive_path = archives_dir / f"{archive_name}.tar.gz"
    try:
        restored = restore_archive(base_path, archive_path, profile)
        click.echo(f"Restored profile '{restored}' from archive '{archive_name}'")
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@archive_group.command("list")
@click.option("--base", default=".", help="Base project path")
def list_cmd(base: str) -> None:
    """List all saved archives."""
    base_path = Path(base).resolve()
    entries = list_archives(base_path)
    if not entries:
        click.echo("No archives found.")
        return
    click.echo(f"{'NAME':<35} {'SIZE':>8}  CREATED")
    click.echo("-" * 65)
    for e in entries:
        size_kb = e["size"] / 1024
        click.echo(f"{e['name']:<35} {size_kb:>7.1f}K  {e['created']}")


@archive_group.command("delete")
@click.argument("archive_name")
@click.option("--base", default=".", help="Base project path")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def delete_cmd(archive_name: str, base: str, yes: bool) -> None:
    """Delete a saved archive."""
    base_path = Path(base).resolve()
    if not yes:
        click.confirm(f"Delete archive '{archive_name}'?", abort=True)
    try:
        delete_archive(base_path, archive_name)
        click.echo(f"Deleted archive '{archive_name}'.")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
