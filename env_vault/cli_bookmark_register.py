"""Registration helper so the bookmark group is attached to the main CLI.

Import and call ``register(cli)`` from env_vault/cli.py to activate.
"""

from __future__ import annotations

import click
from env_vault.cli_bookmark import bookmark_group


def register(cli: click.Group) -> None:
    """Attach the bookmark sub-group to the root CLI group."""
    cli.add_command(bookmark_group)


if __name__ == "__main__":  # pragma: no cover
    # Quick smoke-test: list all registered commands after attachment.
    @click.group()
    def _demo_cli():
        """Demo CLI."""

    register(_demo_cli)
    for name in sorted(_demo_cli.commands):
        print(name)
