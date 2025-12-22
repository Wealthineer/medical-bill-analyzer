"""Stats command - display spending analytics and statistics."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from medical_bill_analyzer.analytics.engine import AnalyticsEngine
from medical_bill_analyzer.database.models import BillFilter
from medical_bill_analyzer.database.repositories.bill_repository import BillRepository
from medical_bill_analyzer.utils.logger import get_logger

from .utils import (
    error_message,
    format_currency,
    get_database_path,
    load_config,
)

logger = get_logger(__name__)
console = Console()


def stats(
    year: Optional[int] = typer.Option(
        None,
        "--year",
        "-y",
        help="Filter by year",
    ),
    practitioner_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by practitioner type (Arzt, Zahnarzt, etc.)",
    ),
    by: str = typer.Option(
        "practitioner",
        "--by",
        "-b",
        help="Group by: practitioner, category, or month",
    ),
    top: Optional[int] = typer.Option(
        None,
        "--top",
        "-n",
        help="Show only top N results (for practitioner stats)",
    ),
):
    """Show spending statistics and analytics.

    Display spending patterns grouped by practitioner, category, or month.

    Examples:

        # Show all practitioners
        medical-bill-analyzer stats --by practitioner

        # Show top 10 practitioners by spending
        medical-bill-analyzer stats --by practitioner --top 10

        # Show category breakdown for 2024
        medical-bill-analyzer stats --by category --year 2024

        # Show monthly trends for 2024
        medical-bill-analyzer stats --by month --year 2024

        # Show dentist spending only
        medical-bill-analyzer stats --by practitioner --type Zahnarzt
    """
    typer.echo()

    # Load config and create engine
    settings = load_config()

    try:
        db_path = get_database_path(settings)
        repository = BillRepository(db_path)
        engine = AnalyticsEngine(repository)

        # Build filter
        filter_obj = BillFilter(year=year, practitioner_type=practitioner_type)

        # Route to appropriate stats function
        if by == "practitioner":
            _display_practitioner_stats(engine, filter_obj, top)
        elif by == "category":
            _display_category_stats(engine, filter_obj)
        elif by == "month":
            _display_monthly_stats(engine, filter_obj)
        else:
            error_message(f"Unknown grouping: {by}")
            typer.secho(
                "\n💡 Valid options: practitioner, category, month",
                fg=typer.colors.YELLOW,
            )
            raise typer.Exit(code=1)

    except Exception as e:
        error_message(f"Failed to calculate statistics: {e}")
        logger.exception("Failed to calculate statistics")
        raise typer.Exit(code=1)


def _display_practitioner_stats(
    engine: AnalyticsEngine,
    filter_obj: Optional[BillFilter],
    top: Optional[int],
):
    """Display practitioner statistics table.

    Args:
        engine: AnalyticsEngine instance
        filter_obj: Optional filter criteria
        top: Optional limit for top N results
    """
    stats = engine.get_practitioner_stats(filter_obj, limit=top)

    if not stats:
        typer.secho("📊 No data found", fg=typer.colors.YELLOW)
        typer.echo()
        return

    # Create Rich table
    title = "Practitioner Statistics"
    if top:
        title += f" (Top {top})"
    if filter_obj and filter_obj.year:
        title += f" - {filter_obj.year}"
    if filter_obj and filter_obj.practitioner_type:
        title += f" - {filter_obj.practitioner_type}"

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Practitioner", style="white", no_wrap=True)
    table.add_column("Type", style="blue")
    table.add_column("Visits", justify="right", style="cyan")
    table.add_column("Total", justify="right", style="green")
    table.add_column("Avg/Visit", justify="right", style="yellow")
    table.add_column("Last Visit", style="magenta")

    # Add rows
    for stat in stats:
        table.add_row(
            stat.practitioner_name or "Unknown",
            stat.practitioner_type or "-",
            str(stat.bill_count),
            format_currency(float(stat.total_amount)),
            format_currency(float(stat.average_amount)),
            stat.last_visit.strftime("%Y-%m-%d") if stat.last_visit else "-",
        )

    # Print table
    console.print(table)

    # Summary
    total = sum(s.total_amount for s in stats)
    total_visits = sum(s.bill_count for s in stats)

    typer.echo()
    typer.echo(f"Showing {len(stats)} practitioner(s)")
    typer.echo(f"Total visits: {total_visits}")
    typer.secho(
        f"Combined total: {format_currency(float(total))}",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo()


def _display_category_stats(
    engine: AnalyticsEngine,
    filter_obj: Optional[BillFilter],
):
    """Display category statistics table with percentages.

    Args:
        engine: AnalyticsEngine instance
        filter_obj: Optional filter criteria
    """
    stats = engine.get_category_stats(filter_obj)

    if not stats:
        typer.secho("📊 No data found", fg=typer.colors.YELLOW)
        typer.echo()
        return

    # Create Rich table
    title = "Category Statistics"
    if filter_obj and filter_obj.year:
        title += f" - {filter_obj.year}"

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Category", style="white")
    table.add_column("Bills", justify="right", style="cyan")
    table.add_column("Total", justify="right", style="green")
    table.add_column("Avg/Bill", justify="right", style="yellow")
    table.add_column("% of Total", justify="right", style="magenta")
    table.add_column("", style="blue")  # Visual bar

    # Add rows with percentage bars
    for stat in stats:
        # Create simple ASCII bar (one char = 5%)
        bar_length = int(stat.percentage_of_total / 5)
        bar = "█" * bar_length

        # Mark major categories (>20%)
        category_name = stat.category
        if stat.is_major_category:
            category_name = f"★ {category_name}"

        table.add_row(
            category_name,
            str(stat.bill_count),
            format_currency(float(stat.total_amount)),
            format_currency(float(stat.average_amount)),
            f"{stat.percentage_of_total:.1f}%",
            bar,
        )

    # Print table
    console.print(table)

    # Summary
    total = sum(s.total_amount for s in stats)
    total_bills = sum(s.bill_count for s in stats)

    typer.echo()
    typer.echo(f"★ = Major category (>20% of spending)")
    typer.echo(f"\nShowing {len(stats)} categories")
    typer.echo(f"Total bills: {total_bills}")
    typer.secho(
        f"Grand total: {format_currency(float(total))}",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo()


def _display_monthly_stats(
    engine: AnalyticsEngine,
    filter_obj: Optional[BillFilter],
):
    """Display monthly trend statistics table.

    Args:
        engine: AnalyticsEngine instance
        filter_obj: Optional filter criteria
    """
    stats = engine.get_monthly_stats(filter_obj)

    if not stats:
        typer.secho("📊 No data found", fg=typer.colors.YELLOW)
        typer.echo()
        return

    # Create Rich table
    title = "Monthly Statistics"
    if filter_obj and filter_obj.year:
        title += f" - {filter_obj.year}"
    if filter_obj and filter_obj.practitioner_type:
        title += f" - {filter_obj.practitioner_type}"

    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Period", style="white")
    table.add_column("Month", style="blue")
    table.add_column("Bills", justify="right", style="cyan")
    table.add_column("Total", justify="right", style="green")
    table.add_column("Avg/Bill", justify="right", style="yellow")

    # Add rows
    for stat in stats:
        table.add_row(
            stat.period,
            stat.month_name,
            str(stat.bill_count),
            format_currency(float(stat.total_amount)),
            format_currency(float(stat.average_amount)),
        )

    # Print table
    console.print(table)

    # Summary
    total = sum(s.total_amount for s in stats)
    total_bills = sum(s.bill_count for s in stats)

    # Calculate average per month
    avg_per_month = total / len(stats) if stats else 0

    typer.echo()
    typer.echo(f"Showing {len(stats)} months")
    typer.echo(f"Total bills: {total_bills}")
    typer.echo(f"Average per month: {format_currency(float(avg_per_month))}")
    typer.secho(
        f"Total: {format_currency(float(total))}",
        fg=typer.colors.GREEN,
        bold=True,
    )
    typer.echo()
