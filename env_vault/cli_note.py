"""CLI commands for managing per-key notes."""

from __future__ import annotations

import os

import click

from env_vault.note import clear_notes, get_note, list_notes, remove_note, set_note


@click.group("note")
def note_group() -> None:
    """Attach human-readable notes to individual env keys."""


def _base() -> str:
    return os.environ.get("ENV_VAULT_BASE", ".")


def _profile() -> str:
    return os.environ.get("ENV_VAULT_PROFILE", "default")


@note_group.command("set")
@click.argument("key")
@click.argument("note")
def set_cmd(key: str, note: str) -> None:
    """Attach NOTE to KEY."""
    set_note(key, note, _base(), _profile())
    click.echo(f"Note set for {key.upper()}.")


@note_group.command("get")
@click.argument("key")
def get_cmd(key: str) -> None:
    """Print the note attached to KEY."""
    note = get_note(key, _base(), _profile())
    if note is None:
        click.echo(f"No note for {key.upper()}.")
    else:
        click.echo(note)


@note_group.command("remove")
@click.argument("key")
def remove_cmd(key: str) -> None:
    """Remove the note attached to KEY."""
    existed = remove_note(key, _base(), _profile())
    if existed:
        click.echo(f"Note removed for {key.upper()}.")
    else:
        click.echo(f"No note found for {key.upper()}.")


@note_group.command("list")
def list_cmd() -> None:
    """List all notes for the active profile."""
    notes = list_notes(_base(), _profile())
    if not notes:
        click.echo("No notes recorded.")
        return
    for key, note in sorted(notes.items()):
        click.echo(f"  {key}: {note}")


@note_group.command("clear")
@click.confirmation_option(prompt="Remove ALL notes for this profile?")
def clear_cmd() -> None:
    """Delete every note for the active profile."""
    count = clear_notes(_base(), _profile())
    click.echo(f"Cleared {count} note(s).")
