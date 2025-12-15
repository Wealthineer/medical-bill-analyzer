"""Total command - Calculate total costs."""

from datetime import date
from typing import Optional

import typer

from medical_bill_analyzer.core.bonus_calculator import BonusCalculator
from medical_bill_analyzer.database.models import BillFilter
from medical_bill_analyzer.database.repositories.bill_repository import BillRepository
from medical_bill_analyzer.utils.logger import get_logger

from .utils import (
    error_message,
    format_currency,
    get_database_path,
    load_config,
    success_message,
)

logger = get_logger(__name__)


def total(
    year: Optional[int] = typer.Option(
        None,
        "--year",
        "-y",
        help="Calculate total for specific year",
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
    practitioner_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by practitioner type (Arzt, Zahnarzt, etc.)",
    ),
):
    """Calculate total medical costs with optional filtering."""
    typer.echo()

    # Load config
    settings = load_config()

    # Parse dates
    from_date = None
    to_date = None

    if start_date:
        try:
            from_date = date.fromisoformat(start_date)
        except ValueError:
            error_message(f"Invalid start date format: {start_date}")
            typer.echo("Use YYYY-MM-DD format\n")
            raise typer.Exit(code=1)

    if end_date:
        try:
            to_date = date.fromisoformat(end_date)
        except ValueError:
            error_message(f"Invalid end date format: {end_date}")
            typer.echo("Use YYYY-MM-DD format\n")
            raise typer.Exit(code=1)

    # Calculate total
    try:
        db_path = get_database_path(settings)
        repository = BillRepository(db_path)
        calculator = BonusCalculator(repository)

        # Create filter if needed
        filter_obj = None
        if practitioner_type or (not year and not from_date):
            filter_obj = BillFilter(
                year=year,
                start_date=from_date,
                end_date=to_date,
                practitioner_type=practitioner_type,
            )

        # Calculate
        if filter_obj:
            total_amount = calculator.calculate_total(filter_obj=filter_obj)
        elif year:
            total_amount = calculator.calculate_total(year=year)
        elif from_date and to_date:
            total_amount = calculator.calculate_total(
                from_date=from_date, to_date=to_date
            )
        else:
            total_amount = calculator.calculate_total()

        # Display result
        _display_total(total_amount, year, from_date, to_date, practitioner_type)

    except Exception as e:
        error_message(f"Failed to calculate total: {e}")
        logger.exception("Failed to calculate total")
        raise typer.Exit(code=1)


def _display_total(
    total_amount,
    year: Optional[int],
    from_date: Optional[date],
    to_date: Optional[date],
    practitioner_type: Optional[str],
):
    """Display total with context.

    Args:
        total_amount: Total amount (Decimal)
        year: Year filter
        from_date: Start date filter
        to_date: End date filter
        practitioner_type: Practitioner type filter
    """
    typer.echo("=" * 50)
    typer.secho("Total Medical Costs", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 50)

    # Show filter context
    if year:
        typer.echo(f"\nYear: {year}")
    elif from_date and to_date:
        typer.echo(f"\nPeriod: {from_date} to {to_date}")
    elif from_date:
        typer.echo(f"\nFrom: {from_date}")
    elif to_date:
        typer.echo(f"\nUntil: {to_date}")
    else:
        typer.echo("\nAll bills")

    if practitioner_type:
        typer.echo(f"Type: {practitioner_type}")

    # Show total
    typer.echo()
    typer.secho(
        f"Total: {format_currency(float(total_amount))}",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo("\n" + "=" * 50 + "\n")
