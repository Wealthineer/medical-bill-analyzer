"""Add command - Add single bill or batch of bills."""

from pathlib import Path
from typing import List, Optional

import typer

from medical_bill_analyzer.core.bill_processor import BillProcessor
from medical_bill_analyzer.database.repositories.bill_repository import BillRepository
from medical_bill_analyzer.extraction.extractor import BillExtractor
from medical_bill_analyzer.llm.factory import create_llm_provider
from medical_bill_analyzer.utils.logger import get_logger

from .utils import (
    error_message,
    format_currency,
    get_database_path,
    info_message,
    load_config,
    success_message,
    warning_message,
)

logger = get_logger(__name__)


def add(
    paths: List[Path] = typer.Argument(
        ...,
        help="PDF file(s) or directory to process",
        exists=True,
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        "-n",
        help="Optional notes to attach to bill(s)",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Process directories recursively",
    ),
):
    """Add medical bill(s) from PDF file(s)."""
    typer.echo()

    # Load config
    settings = load_config()

    # Collect PDF files
    pdf_files = _collect_pdf_files(paths, recursive)

    if not pdf_files:
        error_message("No PDF files found")
        raise typer.Exit(code=1)

    info_message(f"Found {len(pdf_files)} PDF file(s) to process\n")

    # Create components
    try:
        llm_provider = create_llm_provider(settings.llm.provider, settings.llm.get_provider_config())
        extractor = BillExtractor(llm_provider)
        db_path = get_database_path(settings)
        repository = BillRepository(db_path)

        # Setup storage path if configured
        storage_path = None
        if settings.storage.pdf_storage_path:
            storage_path = Path(settings.storage.pdf_storage_path).expanduser()

        processor = BillProcessor(extractor, repository, storage_path)

    except Exception as e:
        error_message(f"Initialization failed: {e}")
        raise typer.Exit(code=1)

    # Process bills
    if len(pdf_files) == 1:
        _process_single_bill(processor, pdf_files[0], notes)
    else:
        _process_multiple_bills(processor, pdf_files, notes)


def _collect_pdf_files(paths: List[Path], recursive: bool) -> List[Path]:
    """Collect PDF files from provided paths.

    Args:
        paths: List of file or directory paths
        recursive: Whether to search directories recursively

    Returns:
        List of PDF file paths
    """
    pdf_files = []

    for path in paths:
        if path.is_file() and path.suffix.lower() == ".pdf":
            pdf_files.append(path)
        elif path.is_dir():
            pattern = "**/*.pdf" if recursive else "*.pdf"
            pdf_files.extend(path.glob(pattern))

    return sorted(set(pdf_files))


def _process_single_bill(
    processor: BillProcessor,
    pdf_path: Path,
    notes: Optional[str],
):
    """Process a single bill with progress indication.

    Args:
        processor: BillProcessor instance
        pdf_path: Path to PDF file
        notes: Optional notes
    """
    typer.secho(f"Processing: {pdf_path.name}", fg=typer.colors.CYAN)

    with typer.progressbar(length=1, label="Extracting and saving") as progress:
        try:
            result = processor.process_single_bill(pdf_path, notes)
            progress.update(1)
            typer.echo()

            if result.total_processed > 0:
                bill_id = result.successful[0]
                extraction = result.extraction_results[0]

                success_message("Bill added successfully!")
                typer.echo(f"\n  ID: {bill_id}")
                if extraction.practitioner_name:
                    typer.echo(f"  Practitioner: {extraction.practitioner_name}")
                if extraction.bill_date:
                    typer.echo(f"  Date: {extraction.bill_date}")
                if extraction.total_amount:
                    typer.echo(f"  Amount: {format_currency(extraction.total_amount)}")
                typer.echo()

            elif result.total_skipped > 0:
                _, reason = result.skipped[0]
                warning_message(f"Bill skipped: {reason}\n")

            elif result.total_failed > 0:
                _, error = result.failed[0]
                error_message(f"Processing failed: {error}\n")

        except Exception as e:
            progress.update(1)
            typer.echo()
            error_message(f"Processing failed: {e}\n")
            logger.exception("Failed to process bill")


def _process_multiple_bills(
    processor: BillProcessor,
    pdf_files: List[Path],
    notes: Optional[str],
):
    """Process multiple bills with progress indication.

    Args:
        processor: BillProcessor instance
        pdf_files: List of PDF file paths
        notes: Optional notes
    """
    typer.secho("Processing bills:", fg=typer.colors.CYAN)
    typer.echo()

    with typer.progressbar(
        pdf_files,
        label="Processing",
        item_show_func=lambda p: p.name if p else "",
    ) as progress:
        try:
            result = processor.process_multiple_bills(list(progress), notes)

            typer.echo()
            typer.echo("\n" + "=" * 50)
            typer.secho("Processing Summary", fg=typer.colors.CYAN, bold=True)
            typer.echo("=" * 50)

            typer.echo(f"\nTotal files:     {result.total_bills}")
            typer.secho(f"Processed:       {result.total_processed}", fg=typer.colors.GREEN)
            if result.total_skipped > 0:
                typer.secho(f"Skipped:         {result.total_skipped}", fg=typer.colors.YELLOW)
            if result.total_failed > 0:
                typer.secho(f"Failed:          {result.total_failed}", fg=typer.colors.RED)

            typer.echo(f"Success rate:    {result.success_rate:.1f}%")

            # Show details for skipped/failed
            if result.skipped:
                typer.echo("\n" + "-" * 50)
                typer.secho("Skipped:", fg=typer.colors.YELLOW)
                for path, reason in result.skipped:
                    typer.echo(f"  • {Path(path).name}: {reason}")

            if result.failed:
                typer.echo("\n" + "-" * 50)
                typer.secho("Failed:", fg=typer.colors.RED)
                for path, error in result.failed:
                    typer.echo(f"  • {Path(path).name}: {error}")

            typer.echo("\n" + "=" * 50 + "\n")

        except Exception as e:
            typer.echo()
            error_message(f"Batch processing failed: {e}\n")
            logger.exception("Failed to process bills")
            raise typer.Exit(code=1)
