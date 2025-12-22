"""Main Typer CLI application."""

import typer

from medical_bill_analyzer import __version__

# Create main app
app = typer.Typer(
    name="medical-bill-analyzer",
    help="Analyze German private health insurance (PKV) medical bills",
    add_completion=False,
)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        typer.echo(f"medical-bill-analyzer version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
):
    """Medical Bill Analyzer CLI - Analyze German PKV medical bills and optimize bonus decisions."""
    pass


# Import and register commands
from medical_bill_analyzer.cli import (
    add_cmd,
    bonus_cmd,
    list_cmd,
    setup_cmd,
    stats_cmd,
    total_cmd,
)

app.command(name="setup")(setup_cmd.setup)
app.command(name="add")(add_cmd.add)
app.command(name="list")(list_cmd.list_bills)
app.command(name="total")(total_cmd.total)
app.command(name="bonus-check")(bonus_cmd.bonus_check)
app.command(name="stats")(stats_cmd.stats)
