"""List command - List bills with filtering."""

from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from medical_bill_analyzer.database.models import BillFilter
from medical_bill_analyzer.database.repositories.bill_repository import BillRepository
from medical_bill_analyzer.utils.logger import get_logger

from .utils import (
    error_message,
    format_currency,
    get_database_path,
    info_message,
    load_config,
)

logger = get_logger(__name__)
console = Console()


def list_bills(
    year: Optional[int] = typer.Option(
        None,
        "--year",
        "-y",
        help="Filter by year",
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--from",
        help="Start date (YYYY-MM-DD)",
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--to",
        help="End date (YYYY-MM-DD)",
    ),
    practitioner: Optional[str] = typer.Option(
        None,
        "--practitioner",
        "-p",
        help="Filter by practitioner name",
    ),
    practitioner_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by practitioner type (Arzt, Zahnarzt, etc.)",
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by extraction status (success, needs_review, failed)",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of bills to show",
    ),
):
    """List medical bills with optional filtering."""
    typer.echo()

    # Load config
    settings = load_config()

    # Create filter
    bill_filter = _create_filter(
        year, start_date, end_date, practitioner, practitioner_type, status
    )

    # Get bills
    try:
        db_path = get_database_path(settings)
        repository = BillRepository(db_path)

        bills = repository.filter(bill_filter)

        if limit:
            bills = bills[:limit]

        if not bills:
            info_message("No bills found matching the criteria")
            typer.echo()
            return

        # Display bills
        _display_bills_table(bills)

        # Show summary
        total_amount = sum(bill.total_amount or 0 for bill in bills)
        typer.echo(f"\nShowing {len(bills)} bill(s)")
        typer.echo(f"Total amount: {format_currency(float(total_amount))}\n")

    except Exception as e:
        error_message(f"Failed to list bills: {e}")
        logger.exception("Failed to list bills")
        raise typer.Exit(code=1)


def _create_filter(
    year: Optional[int],
    start_date_str: Optional[str],
    end_date_str: Optional[str],
    practitioner: Optional[str],
    practitioner_type: Optional[str],
    status: Optional[str],
) -> BillFilter:
    """Create BillFilter from command options.

    Args:
        year: Year filter
        start_date_str: Start date string
        end_date_str: End date string
        practitioner: Practitioner name filter
        practitioner_type: Practitioner type filter
        status: Status filter

    Returns:
        BillFilter object
    """
    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            error_message(f"Invalid start date format: {start_date_str}")
            typer.echo("Use YYYY-MM-DD format\n")
            raise typer.Exit(code=1)

    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            error_message(f"Invalid end date format: {end_date_str}")
            typer.echo("Use YYYY-MM-DD format\n")
            raise typer.Exit(code=1)

    return BillFilter(
        year=year,
        start_date=start_date,
        end_date=end_date,
        practitioner_name=practitioner,
        practitioner_type=practitioner_type,
        status=status,
    )


def _display_bills_table(bills):
    """Display bills in a formatted table.

    Args:
        bills: List of Bill objects
    """
    table = Table(title="Medical Bills", show_header=True, header_style="bold cyan")

    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Date", style="white")
    table.add_column("Practitioner", style="white", max_width=30)
    table.add_column("Type", style="white")
    table.add_column("Amount", justify="right", style="green")
    table.add_column("Status", justify="center")

    for bill in bills:
        # Format date
        bill_date = bill.bill_date.strftime("%Y-%m-%d") if bill.bill_date else "-"

        # Format practitioner
        practitioner = bill.practitioner_name or "-"
        if len(practitioner) > 30:
            practitioner = practitioner[:27] + "..."

        # Format type
        prac_type = bill.practitioner_type or "-"

        # Format amount
        amount = (
            format_currency(float(bill.total_amount))
            if bill.total_amount
            else "-"
        )

        # Format status
        status_map = {
            "success": "[green]✓[/green]",
            "needs_review": "[yellow]⚠[/yellow]",
            "failed": "[red]✗[/red]",
        }
        status = status_map.get(bill.extraction_status, bill.extraction_status)

        table.add_row(
            str(bill.id),
            bill_date,
            practitioner,
            prac_type,
            amount,
            status,
        )

    console.print(table)
