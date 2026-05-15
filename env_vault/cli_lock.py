"""CLI commands for vault lock management."""

from __future__ import annotations

import os
from pathlib import Path

import click

from env_vault.lock import acquire_lock, release_lock, is_locked, lock_info


@click.group("lock")
def lock_group() -> None:
    """Manage the vault advisory lock."""


@lock_group.command("status")
@click.option("--base", default=None, help="Base directory of the vault.")
def status_cmd(base: str | None) -> None:
    """Show whether the vault is currently locked."""
    base_path = Path(base) if base else Path(os.environ.get("VAULT_BASE", "."))
    info = lock_info(base_path)
    if info is None:
        click.echo("Vault is unlocked.")
    else:
        click.echo(
            f"Vault is LOCKED — pid={info.get('pid')}, "
            f"age={info.get('age_seconds')}s"
        )


@lock_group.command("acquire")
@click.option("--base", default=None, help="Base directory of the vault.")
@click.option("--timeout", default=10, show_default=True, help="Seconds to wait.")
def acquire_cmd(base: str | None, timeout: int) -> None:
    """Manually acquire the vault lock (for scripting)."""
    base_path = Path(base) if base else Path(os.environ.get("VAULT_BASE", "."))
    try:
        acquire_lock(base_path, timeout=timeout)
        click.echo("Lock acquired.")
    except TimeoutError as exc:
        raise click.ClickException(str(exc)) from exc


@lock_group.command("release")
@click.option("--base", default=None, help="Base directory of the vault.")
def release_cmd(base: str | None) -> None:
    """Release the vault lock held by this process."""
    base_path = Path(base) if base else Path(os.environ.get("VAULT_BASE", "."))
    if not is_locked(base_path):
        click.echo("Vault is not locked — nothing to release.")
        return
    release_lock(base_path)
    click.echo("Lock released.")
