"""Entry point for running env-vault as a module: python -m env_vault.

This allows the package to be invoked directly via:
    python -m env_vault [OPTIONS] COMMAND [ARGS]...
"""

from env_vault.cli import cli

if __name__ == "__main__":
    cli()
