"""CLI commands for export and import of vault bundles."""

import click
from pathlib import Path

from env_vault.export import export_vault, import_vault, decrypt_to_plaintext


@click.group()
def export_group():
    """Commands for exporting and importing vault bundles."""
    pass


@export_group.command("export")
@click.argument("project")
@click.argument("output", type=click.Path())
@click.option(
    "--base-path",
    default=str(Path.home()),
    show_default=True,
    help="Base directory for vault storage.",
)
def export_cmd(project: str, output: str, base_path: str):
    """Export PROJECT vault to OUTPUT bundle file."""
    output_path = Path(output)
    base = Path(base_path)
    try:
        export_vault(project, output_path, base)
        click.echo(f"Vault '{project}' exported to {output_path}")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@export_group.command("import")
@click.argument("bundle", type=click.Path(exists=True))
@click.option(
    "--base-path",
    default=str(Path.home()),
    show_default=True,
    help="Base directory for vault storage.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing vault if present.",
)
def import_cmd(bundle: str, base_path: str, overwrite: bool):
    """Import a vault from a BUNDLE file."""
    bundle_path = Path(bundle)
    base = Path(base_path)
    try:
        project = import_vault(bundle_path, base, overwrite=overwrite)
        click.echo(f"Vault '{project}' imported successfully.")
    except FileExistsError as e:
        click.echo(f"Error: {e}\nUse --overwrite to replace existing vault.", err=True)
        raise SystemExit(1)


@export_group.command("plaintext")
@click.argument("project")
@click.option(
    "--base-path",
    default=str(Path.home()),
    show_default=True,
    help="Base directory for vault storage.",
)
def plaintext_cmd(project: str, base_path: str):
    """Print decrypted .env contents for PROJECT to stdout."""
    base = Path(base_path)
    try:
        content = decrypt_to_plaintext(project, base)
        click.echo(content, nl=False)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
