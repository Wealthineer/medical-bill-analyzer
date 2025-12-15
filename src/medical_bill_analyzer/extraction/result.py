"""Extraction result models."""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ExtractionStatus(str, Enum):
    """Status of extraction operation."""

    SUCCESS = "success"
    PDF_INVALID = "pdf_invalid"
    PDF_NOT_PROCESSABLE = "pdf_not_processable"
    EXTRACTION_FAILED = "extraction_failed"
    VALIDATION_FAILED = "validation_failed"


@dataclass
class ExtractionResult:
    """Result of bill information extraction.

    This class contains the outcome of extracting information from a medical
    bill PDF, including the extracted data, status, and any errors or warnings.

    Attributes:
        status: Status of the extraction operation
        pdf_path: Path to the PDF file that was processed
        pdf_hash: SHA256 hash of the PDF file
        extracted_data: Dictionary of extracted information (if successful)
        errors: List of error messages encountered
        warnings: List of warning messages
        practitioner_name: Extracted practitioner name (for convenience)
        practitioner_type: Extracted practitioner type (for convenience)
        bill_date: Extracted bill date (for convenience)
        bill_number: Extracted bill number (for convenience)
        total_amount: Extracted total amount (for convenience)
        currency: Extracted currency (for convenience)

    Example:
        >>> result = ExtractionResult(
        ...     status=ExtractionStatus.SUCCESS,
        ...     pdf_path=Path("bill.pdf"),
        ...     pdf_hash="abc123",
        ...     extracted_data={"practitioner_name": "Dr. Smith", ...}
        ... )
        >>> if result.is_success:
        ...     print(f"Extracted: {result.practitioner_name}")
    """

    status: ExtractionStatus
    pdf_path: Path
    pdf_hash: str
    extracted_data: Optional[dict] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Convenience properties from extracted_data
    practitioner_name: Optional[str] = None
    practitioner_type: Optional[str] = None
    bill_date: Optional[date] = None
    bill_number: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if extraction was successful."""
        return self.status == ExtractionStatus.SUCCESS

    @property
    def is_processable(self) -> bool:
        """Check if PDF was processable (valid and not scanned)."""
        return self.status not in [
            ExtractionStatus.PDF_INVALID,
            ExtractionStatus.PDF_NOT_PROCESSABLE,
        ]

    def __post_init__(self):
        """Populate convenience properties from extracted_data."""
        if self.extracted_data:
            self.practitioner_name = self.extracted_data.get("practitioner_name")
            self.practitioner_type = self.extracted_data.get("practitioner_type")
            self.bill_date = self.extracted_data.get("bill_date")
            self.bill_number = self.extracted_data.get("bill_number")
            self.total_amount = self.extracted_data.get("total_amount")
            self.currency = self.extracted_data.get("currency", "EUR")

    def to_dict(self) -> dict:
        """Convert result to dictionary for serialization.

        Returns:
            Dictionary representation of the extraction result
        """
        return {
            "status": self.status.value,
            "pdf_path": str(self.pdf_path),
            "pdf_hash": self.pdf_hash,
            "extracted_data": self.extracted_data,
            "errors": self.errors,
            "warnings": self.warnings,
            "practitioner_name": self.practitioner_name,
            "practitioner_type": self.practitioner_type,
            "bill_date": self.bill_date.isoformat() if self.bill_date else None,
            "bill_number": self.bill_number,
            "total_amount": self.total_amount,
            "currency": self.currency,
        }
