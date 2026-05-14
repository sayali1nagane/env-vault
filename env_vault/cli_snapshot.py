"""CLI commands for vault snapshot management."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click

from .snapshot import list_snapshots, create_snapshot, restore_snapshot, delete_snapshot


@click.group("snapshot")
def snapshot_group() -> None:
    """Manage vault snapshots."""


@snapshot_group.command("save")
@click.option("--label", "-l", default="", help="Optional human-readable label.")
@click.option("--base", default=".", help="Project base path.", show_default=True)
def save_cmd(label: str, base: str) -> None:
    """Save a snapshot of the current vault."""
    base_path = Path(base)
    try:
        meta = create_snapshot(base_path, label or None)
        ts = datetime.fromtimestamp(meta["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"Snapshot saved: {meta['id']}  [{ts}]" + (f"  label={meta['label']}" if meta["label"] else ""))
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_group.command("list")
@click.option("--base", default=".", help="Project base path.", show_default=True)
def list_cmd(base: str) -> None:
    """List all saved snapshots."""
    snapshots = list_snapshots(Path(base))
    if not snapshots:
        click.echo("No snapshots found.")
        return
    for s in snapshots:
        ts = datetime.fromtimestamp(s["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        label_part = f"  {s['label']}" if s.get("label") else ""
        click.echo(f"{s['id']}  {ts}{label_part}")


@snapshot_group.command("restore")
@click.argument("snap_id")
@click.option("--base", default=".", help="Project base path.", show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def restore_cmd(snap_id: str, base: str, yes: bool) -> None:
    """Restore vault from a snapshot."""
    if not yes:
        click.confirm(f"Restore snapshot '{snap_id}'? This will overwrite the current vault.", abort=True)
    try:
        restore_snapshot(Path(base), snap_id)
        click.echo(f"Vault restored from snapshot '{snap_id}'.")
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@snapshot_group.command("delete")
@click.argument("snap_id")
@click.option("--base", default=".", help="Project base path.", show_default=True)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def delete_cmd(snap_id: str, base: str, yes: bool) -> None:
    """Delete a snapshot."""
    if not yes:
        click.confirm(f"Delete snapshot '{snap_id}'?", abort=True)
    delete_snapshot(Path(base), snap_id)
    click.echo(f"Snapshot '{snap_id}' deleted.")
