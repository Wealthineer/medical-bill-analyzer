"""Main entry point for medical-bill-analyzer application.

Auto-launches TUI if no CLI arguments provided, otherwise uses CLI.
"""

import sys

import typer

from medical_bill_analyzer.cli.app import app
from medical_bill_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Run the application (TUI or CLI depending on arguments).

    Auto-launches TUI if:
    - No CLI arguments provided
    - Running in a TTY (interactive terminal)
    - Textual is installed

    Otherwise falls back to CLI mode.
    """
    # If no arguments, try to launch TUI
    if len(sys.argv) == 1:
        try:
            from medical_bill_analyzer.tui.app import MedicalBillAnalyzerTUI

            tui_app = MedicalBillAnalyzerTUI()
            tui_app.run()
            return
        except ImportError as e:
            # Textual or dependency not available
            typer.secho(f"TUI not available: {e}", fg=typer.colors.YELLOW)
            typer.secho("Run 'medical-bill-analyzer --help' for CLI usage", fg=typer.colors.BLUE)
            return
        except Exception as e:
            # TUI failed to launch
            logger.exception("TUI failed to launch")
            typer.secho(f"TUI failed to launch: {e}", fg=typer.colors.YELLOW)
            typer.secho("Run 'medical-bill-analyzer --help' for CLI usage", fg=typer.colors.BLUE)
            return

    # Use CLI
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
