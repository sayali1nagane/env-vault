"""CLI commands for comparing profiles."""

import os
import click
from env_vault.compare import compare_profiles


@click.group(name="compare")
def compare_group():
    """Compare env variables across profiles."""


@compare_group.command(name="profiles")
@click.argument("profile_a")
@click.argument("profile_b")
@click.option("--show-values", is_flag=True, default=False, help="Show differing values side by side.")
@click.option("--base-path", default=None, help="Base path for vault storage.")
def profiles_cmd(profile_a: str, profile_b: str, show_values: bool, base_path: str):
    """Compare two profiles and display differences."""
    base = base_path or os.environ.get("ENV_VAULT_PATH", ".")

    try:
        result = compare_profiles(base, profile_a, profile_b, show_values=show_values)
    except FileNotFoundError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    click.echo(f"Comparing '{profile_a}' vs '{profile_b}'\n")

    if result["only_in_a"]:
        click.echo(f"  Only in '{profile_a}':")
        for k in result["only_in_a"]:
            click.echo(f"    - {k}")

    if result["only_in_b"]:
        click.echo(f"  Only in '{profile_b}':")
        for k in result["only_in_b"]:
            click.echo(f"    - {k}")

    if result["in_both_different"]:
        click.echo("  Different values:")
        for entry in result["in_both_different"]:
            if show_values:
                click.echo(f"    ~ {entry['key']}")
                click.echo(f"        {profile_a}: {entry['value_a']}")
                click.echo(f"        {profile_b}: {entry['value_b']}")
            else:
                click.echo(f"    ~ {entry['key']}")

    if result["in_both_same"]:
        click.echo(f"  Same in both ({len(result['in_both_same'])} keys): " +
                   ", ".join(result["in_both_same"]))

    if not any([result["only_in_a"], result["only_in_b"], result["in_both_different"]]):
        click.echo("  Profiles are identical.")
