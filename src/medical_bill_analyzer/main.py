"""Main entry point for medical-bill-analyzer CLI application."""

import sys

import typer

from medical_bill_analyzer.cli.app import app
from medical_bill_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.exception("Unexpected error")
        typer.secho(f"\nError: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
