"""CLI commands for managing env-vault bookmarks."""

from __future__ import annotations

import os
import click
from env_vault.bookmark import (
    list_bookmarks,
    set_bookmark,
    get_bookmark,
    remove_bookmark,
    find_bookmarks_for_key,
)


@click.group(name="bookmark")
def bookmark_group():
    """Manage bookmarks for frequently used env keys."""


@bookmark_group.command(name="add")
@click.argument("name")
@click.argument("key")
@click.argument("profile")
@click.option("--note", default="", help="Optional description for this bookmark.")
def add_cmd(name: str, key: str, profile: str, note: str):
    """Add or update a bookmark NAME pointing to KEY in PROFILE."""
    base = os.environ.get("ENV_VAULT_BASE", ".")
    try:
        entry = set_bookmark(base, name, key, profile, note)
        click.echo(f"Bookmarked '{name}' -> {entry['profile']}:{entry['key']}")
        if note:
            click.echo(f"  Note: {note}")
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@bookmark_group.command(name="get")
@click.argument("name")
def get_cmd(name: str):
    """Show details of a single bookmark."""
    base = os.environ.get("ENV_VAULT_BASE", ".")
    entry = get_bookmark(base, name)
    if entry is None:
        click.echo(f"No bookmark named '{name}'.", err=True)
        raise SystemExit(1)
    click.echo(f"Name   : {name}")
    click.echo(f"Key    : {entry['key']}")
    click.echo(f"Profile: {entry['profile']}")
    if entry.get("note"):
        click.echo(f"Note   : {entry['note']}")


@bookmark_group.command(name="remove")
@click.argument("name")
def remove_cmd(name: str):
    """Remove a bookmark by NAME."""
    base = os.environ.get("ENV_VAULT_BASE", ".")
    if remove_bookmark(base, name):
        click.echo(f"Removed bookmark '{name}'.")
    else:
        click.echo(f"Bookmark '{name}' not found.", err=True)
        raise SystemExit(1)


@bookmark_group.command(name="list")
def list_cmd():
    """List all bookmarks."""
    base = os.environ.get("ENV_VAULT_BASE", ".")
    bookmarks = list_bookmarks(base)
    if not bookmarks:
        click.echo("No bookmarks saved.")
        return
    for name, entry in bookmarks.items():
        note_part = f"  # {entry['note']}" if entry.get("note") else ""
        click.echo(f"  {name:<20} {entry['profile']}:{entry['key']}{note_part}")


@bookmark_group.command(name="find")
@click.argument("key")
def find_cmd(key: str):
    """Find all bookmarks referencing KEY."""
    base = os.environ.get("ENV_VAULT_BASE", ".")
    results = find_bookmarks_for_key(base, key)
    if not results:
        click.echo(f"No bookmarks found for key '{key.upper()}'.")
        return
    for item in results:
        click.echo(f"  {item['name']:<20} {item['profile']}:{item['key']}")
