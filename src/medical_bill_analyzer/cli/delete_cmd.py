"""Delete command - Remove bills from the database."""

from typing import Optional

import typer

from medical_bill_analyzer.database.repositories.bill_repository import BillRepository
from medical_bill_analyzer.utils.logger import get_logger

from .utils import (
    confirm_action,
    error_message,
    format_currency,
    get_database_path,
    info_message,
    load_config,
    success_message,
)

logger = get_logger(__name__)


def delete(
    bill_id: int = typer.Argument(..., help="ID of the bill to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Delete without confirmation",
    ),
):
    """Delete a medical bill from the database.

    The bill ID can be found using the 'list' command.

    Examples:

        # Delete bill with ID 5 (with confirmation)
        medical-bill-analyzer delete 5

        # Delete bill with ID 10 without confirmation
        medical-bill-analyzer delete 10 --force
    """
    typer.echo()

    # Load config
    settings = load_config()

    try:
        db_path = get_database_path(settings)
        repository = BillRepository(db_path)

        # Get the bill first to show details
        bill = repository.get_by_id(bill_id)

        if not bill:
            error_message(f"Bill with ID {bill_id} not found")
            typer.echo()
            typer.secho(
                "\n💡 Use 'medical-bill-analyzer list' to see all bills and their IDs",
                fg=typer.colors.YELLOW,
            )
            typer.echo()
            raise typer.Exit(code=1)

        # Show bill details
        typer.echo("Bill to delete:")
        typer.echo(f"  ID: {bill.id}")
        if bill.bill_date:
            typer.echo(f"  Date: {bill.bill_date.strftime('%Y-%m-%d')}")
        if bill.practitioner_name:
            typer.echo(f"  Practitioner: {bill.practitioner_name}")
        if bill.practitioner_type:
            typer.echo(f"  Type: {bill.practitioner_type}")
        if bill.total_amount:
            typer.echo(f"  Amount: {format_currency(float(bill.total_amount))}")
        typer.echo()

        # Confirm deletion
        if not force:
            confirmed = confirm_action(
                f"Are you sure you want to delete bill #{bill_id}?",
                default=False,
            )
            if not confirmed:
                info_message("Deletion cancelled")
                typer.echo()
                return

        # Delete the bill
        deleted = repository.delete(bill_id)

        if deleted:
            success_message(f"Bill #{bill_id} deleted successfully")
            typer.echo()
        else:
            error_message(f"Failed to delete bill #{bill_id}")
            typer.echo()
            raise typer.Exit(code=1)

    except Exception as e:
        error_message(f"Failed to delete bill: {e}")
        logger.exception("Failed to delete bill")
        raise typer.Exit(code=1)
