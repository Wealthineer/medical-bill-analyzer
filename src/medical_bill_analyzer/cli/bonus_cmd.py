"""Bonus check command - Compare costs against bonus threshold."""

from decimal import Decimal
from typing import Optional

import typer

from medical_bill_analyzer.core.bonus_calculator import BonusCalculator
from medical_bill_analyzer.database.repositories.bill_repository import BillRepository
from medical_bill_analyzer.utils.logger import get_logger

from .utils import (
    error_message,
    format_currency,
    get_database_path,
    load_config,
)

logger = get_logger(__name__)


def bonus_check(
    year: Optional[int] = typer.Option(
        None,
        "--year",
        "-y",
        help="Check for specific year (default: current year)",
    ),
    threshold: Optional[float] = typer.Option(
        None,
        "--threshold",
        "-t",
        help="Bonus threshold in EUR (overrides config)",
    ),
):
    """Check if you should keep your bonus or submit claims."""
    typer.echo()

    # Load config
    settings = load_config()

    # Get threshold
    bonus_threshold = Decimal(str(threshold)) if threshold else Decimal(
        str(settings.bonus.default_threshold)
    )

    # Get year (default to current year)
    if year is None:
        from datetime import date
        year = date.today().year

    # Calculate recommendation
    try:
        db_path = get_database_path(settings)
        repository = BillRepository(db_path)
        calculator = BonusCalculator(repository)

        recommendation = calculator.get_recommendation_for_year(year, bonus_threshold)

        # Display result
        _display_recommendation(recommendation, year)

    except Exception as e:
        error_message(f"Failed to calculate recommendation: {e}")
        logger.exception("Failed to calculate recommendation")
        raise typer.Exit(code=1)


def _display_recommendation(recommendation, year: int):
    """Display bonus recommendation in a clear format.

    Args:
        recommendation: BonusRecommendation object
        year: Year
    """
    typer.echo("=" * 60)
    typer.secho("Bonus Recommendation", fg=typer.colors.CYAN, bold=True)
    typer.echo("=" * 60)

    typer.echo(f"\nYear: {year}")
    typer.echo()

    # Show numbers
    typer.echo("Your Costs:")
    typer.secho(
        f"  Total medical costs: {format_currency(float(recommendation.total_amount))}",
        fg=typer.colors.WHITE,
    )
    typer.secho(
        f"  Bonus threshold:     {format_currency(float(recommendation.bonus_threshold))}",
        fg=typer.colors.WHITE,
    )
    typer.secho(
        f"  Difference:          {format_currency(float(recommendation.difference))}",
        fg=typer.colors.WHITE,
    )

    typer.echo()
    typer.echo("-" * 60)
    typer.echo()

    # Show recommendation
    if recommendation.should_keep_bonus:
        typer.secho("✓ RECOMMENDATION: Keep Your Bonus", fg=typer.colors.GREEN, bold=True)
        typer.echo()
        typer.secho(
            f"💰 Potential Savings: {format_currency(float(recommendation.savings))}",
            fg=typer.colors.GREEN,
            bold=True,
        )
    else:
        typer.secho("✓ RECOMMENDATION: Submit Claims", fg=typer.colors.GREEN, bold=True)
        typer.echo()
        typer.secho(
            f"💰 Potential Savings: {format_currency(float(recommendation.savings))}",
            fg=typer.colors.GREEN,
            bold=True,
        )

    typer.echo()
    typer.echo("-" * 60)
    typer.echo()

    # Show explanation
    typer.echo("Explanation:")
    typer.echo(recommendation.explanation)

    typer.echo()
    typer.echo("=" * 60 + "\n")
