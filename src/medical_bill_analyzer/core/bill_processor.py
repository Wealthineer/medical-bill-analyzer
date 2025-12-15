"""Bill processor - orchestrates extraction and database storage."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..database.models import BillCreate
from ..database.repositories.bill_repository import BillRepository
from ..extraction.extractor import BillExtractor
from ..extraction.result import ExtractionResult, ExtractionStatus
from ..utils.logger import get_logger
from .exceptions import DuplicateBillError

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing one or more bills.

    Attributes:
        total_processed: Number of bills successfully processed
        total_skipped: Number of bills skipped (duplicates, invalid, etc.)
        total_failed: Number of bills that failed processing
        successful: List of successful bill IDs
        skipped: List of (pdf_path, reason) tuples for skipped bills
        failed: List of (pdf_path, error) tuples for failed bills
        extraction_results: List of ExtractionResult objects
    """

    total_processed: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    successful: List[int] = field(default_factory=list)
    skipped: List[tuple] = field(default_factory=list)
    failed: List[tuple] = field(default_factory=list)
    extraction_results: List[ExtractionResult] = field(default_factory=list)

    @property
    def total_bills(self) -> int:
        """Total number of bills attempted."""
        return self.total_processed + self.total_skipped + self.total_failed

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_bills == 0:
            return 0.0
        return (self.total_processed / self.total_bills) * 100


class BillProcessor:
    """Processes medical bills: extraction + database storage.

    This class orchestrates the complete bill processing workflow:
    1. Extract information using BillExtractor
    2. Check for duplicates by PDF hash
    3. Save to database
    4. Optionally copy PDF to storage directory

    Example:
        >>> from medical_bill_analyzer.extraction import BillExtractor
        >>> from medical_bill_analyzer.database.repositories import BillRepository
        >>> from medical_bill_analyzer.llm.factory import create_llm_provider
        >>>
        >>> provider = create_llm_provider("anthropic", config)
        >>> extractor = BillExtractor(provider)
        >>> repository = BillRepository(connection)
        >>> processor = BillProcessor(extractor, repository)
        >>>
        >>> result = processor.process_single_bill(Path("bill.pdf"))
        >>> if result.total_processed > 0:
        ...     print(f"Processed bill ID: {result.successful[0]}")
    """

    def __init__(
        self,
        extractor: BillExtractor,
        repository: BillRepository,
        storage_path: Optional[Path] = None,
    ):
        """Initialize bill processor.

        Args:
            extractor: BillExtractor for information extraction
            repository: BillRepository for database operations
            storage_path: Optional path to copy PDFs for storage
        """
        self.extractor = extractor
        self.repository = repository
        self.storage_path = storage_path
        logger.info(
            f"Initialized BillProcessor (storage: {storage_path or 'disabled'})"
        )

    def process_single_bill(
        self, pdf_path: Path, notes: Optional[str] = None
    ) -> ProcessingResult:
        """Process a single bill PDF.

        Args:
            pdf_path: Path to PDF file
            notes: Optional notes about the bill

        Returns:
            ProcessingResult with outcome

        Example:
            >>> result = processor.process_single_bill(Path("bill.pdf"))
            >>> if result.total_processed > 0:
            ...     print("Success!")
        """
        logger.info(f"Processing single bill: {pdf_path}")
        result = ProcessingResult()

        # Step 1: Extract information
        try:
            extraction = self.extractor.extract_from_pdf(pdf_path)
            result.extraction_results.append(extraction)
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            result.failed.append((str(pdf_path), str(e)))
            result.total_failed = 1
            return result

        # Step 2: Check extraction status
        if extraction.status != ExtractionStatus.SUCCESS:
            reason = f"{extraction.status.value}: {', '.join(extraction.errors)}"
            logger.warning(f"Bill not processable: {reason}")
            result.skipped.append((str(pdf_path), reason))
            result.total_skipped = 1
            return result

        # Step 3: Check for duplicate by hash
        try:
            existing = self.repository.get_by_file_hash(extraction.pdf_hash)
            if existing:
                logger.info(f"Duplicate detected (hash: {extraction.pdf_hash[:8]}...)")
                result.skipped.append(
                    (str(pdf_path), f"Duplicate of bill ID {existing.id}")
                )
                result.total_skipped = 1
                return result
        except Exception as e:
            logger.error(f"Duplicate check failed: {e}")
            result.failed.append((str(pdf_path), f"Duplicate check failed: {e}"))
            result.total_failed = 1
            return result

        # Step 4: Create bill record
        try:
            bill_create = BillCreate(
                filename=pdf_path.name,
                file_hash=extraction.pdf_hash,
                pdf_path=str(pdf_path),
                practitioner_name=extraction.practitioner_name,
                practitioner_type=extraction.practitioner_type,
                bill_date=extraction.bill_date,
                bill_number=extraction.bill_number,
                total_amount=extraction.total_amount,
                currency=extraction.currency,
                notes=notes,
            )
            bill = self.repository.create(bill_create)
            logger.info(f"Bill saved to database (ID: {bill.id})")
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            result.failed.append((str(pdf_path), f"Database error: {e}"))
            result.total_failed = 1
            return result

        # Step 5: Copy PDF to storage (if configured)
        if self.storage_path:
            try:
                self._copy_to_storage(pdf_path, extraction.pdf_hash)
            except Exception as e:
                logger.warning(f"Failed to copy PDF to storage: {e}")
                # Don't fail the whole operation for storage copy failure

        # Success!
        result.successful.append(bill.id)
        result.total_processed = 1
        logger.info(f"Successfully processed bill (ID: {bill.id})")
        return result

    def process_multiple_bills(
        self, pdf_paths: List[Path], notes: Optional[str] = None
    ) -> ProcessingResult:
        """Process multiple bill PDFs.

        Args:
            pdf_paths: List of PDF file paths
            notes: Optional notes to apply to all bills

        Returns:
            ProcessingResult with aggregate outcomes

        Example:
            >>> pdf_files = [Path("bill1.pdf"), Path("bill2.pdf")]
            >>> result = processor.process_multiple_bills(pdf_files)
            >>> print(f"Processed: {result.total_processed}/{result.total_bills}")
        """
        logger.info(f"Processing {len(pdf_paths)} bills")
        aggregate_result = ProcessingResult()

        for pdf_path in pdf_paths:
            single_result = self.process_single_bill(pdf_path, notes)

            # Aggregate results
            aggregate_result.total_processed += single_result.total_processed
            aggregate_result.total_skipped += single_result.total_skipped
            aggregate_result.total_failed += single_result.total_failed
            aggregate_result.successful.extend(single_result.successful)
            aggregate_result.skipped.extend(single_result.skipped)
            aggregate_result.failed.extend(single_result.failed)
            aggregate_result.extraction_results.extend(single_result.extraction_results)

        logger.info(
            f"Batch complete: {aggregate_result.total_processed} processed, "
            f"{aggregate_result.total_skipped} skipped, "
            f"{aggregate_result.total_failed} failed"
        )
        return aggregate_result

    def _copy_to_storage(self, pdf_path: Path, pdf_hash: str) -> None:
        """Copy PDF to storage directory.

        Args:
            pdf_path: Source PDF path
            pdf_hash: PDF hash for filename

        Raises:
            Exception: If copy fails
        """
        if not self.storage_path:
            return

        # Create storage directory if needed
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Use hash as filename to avoid conflicts
        dest_path = self.storage_path / f"{pdf_hash}.pdf"

        if dest_path.exists():
            logger.debug(f"PDF already in storage: {dest_path}")
            return

        shutil.copy2(pdf_path, dest_path)
        logger.info(f"Copied PDF to storage: {dest_path}")
