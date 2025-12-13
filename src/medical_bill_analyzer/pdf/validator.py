"""PDF validation and quality checks."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import pdfplumber

from ..core.exceptions import PDFProcessingError
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Minimum text length to consider a PDF as having a text layer
MIN_TEXT_LENGTH = 50  # characters

# Maximum file size in bytes (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024


@dataclass
class ValidationResult:
    """Result of PDF validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    is_scanned: bool = False
    page_count: int = 0
    has_text: bool = False
    file_size_bytes: int = 0

    @property
    def is_processable(self) -> bool:
        """Check if PDF can be processed (valid and not scanned)."""
        return self.is_valid and self.has_text and not self.is_scanned


def validate_pdf(pdf_path: Path) -> ValidationResult:
    """
    Validate a PDF file for processing.

    Checks:
    - File exists and is readable
    - File size is reasonable
    - PDF is not corrupted
    - PDF has text layer (not scanned)
    - PDF is not password-protected

    Args:
        pdf_path: Path to PDF file

    Returns:
        ValidationResult with validation details

    Example:
        >>> result = validate_pdf(Path("bill.pdf"))
        >>> if result.is_processable:
        ...     text = extract_text_from_pdf(pdf_path)
    """
    errors = []
    warnings = []
    is_scanned = False
    page_count = 0
    has_text = False
    file_size = 0

    # Check file exists
    if not pdf_path.exists():
        errors.append(f"File not found: {pdf_path}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            is_scanned=is_scanned,
            page_count=page_count,
            has_text=has_text,
            file_size_bytes=file_size,
        )

    if not pdf_path.is_file():
        errors.append(f"Path is not a file: {pdf_path}")
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            is_scanned=is_scanned,
            page_count=page_count,
            has_text=has_text,
            file_size_bytes=file_size,
        )

    # Check file size
    file_size = pdf_path.stat().st_size
    if file_size == 0:
        errors.append("PDF file is empty")
    elif file_size > MAX_FILE_SIZE:
        warnings.append(
            f"PDF file is large ({file_size / (1024*1024):.1f} MB), "
            "processing may be slow"
        )

    # Try to open and validate PDF
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check page count
            page_count = len(pdf.pages)
            if page_count == 0:
                errors.append("PDF has no pages")
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    is_scanned=is_scanned,
                    page_count=page_count,
                    has_text=has_text,
                    file_size_bytes=file_size,
                )

            # Check for text layer
            total_text_length = 0
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    total_text_length += len(page_text)

            has_text = total_text_length >= MIN_TEXT_LENGTH

            # Determine if scanned
            if total_text_length < MIN_TEXT_LENGTH:
                is_scanned = True
                warnings.append(
                    "PDF appears to be scanned (no or minimal text layer). "
                    "OCR would be required for processing."
                )

            logger.info(
                f"PDF validation: {page_count} pages, "
                f"{total_text_length} characters, "
                f"scanned={is_scanned}"
            )

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError as e:
        errors.append(f"PDF is corrupted or malformed: {e}")

    except pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect:
        errors.append("PDF is password-protected")

    except Exception as e:
        errors.append(f"Failed to validate PDF: {e}")

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        is_scanned=is_scanned,
        page_count=page_count,
        has_text=has_text,
        file_size_bytes=file_size,
    )


def is_scanned_pdf(pdf_path: Path) -> bool:
    """
    Check if a PDF appears to be scanned (image-only, no text layer).

    Args:
        pdf_path: Path to PDF file

    Returns:
        True if PDF appears to be scanned, False otherwise

    Raises:
        PDFProcessingError: If PDF cannot be read

    Example:
        >>> if is_scanned_pdf(Path("bill.pdf")):
        ...     print("This PDF requires OCR")
    """
    result = validate_pdf(pdf_path)

    if not result.is_valid:
        raise PDFProcessingError(
            f"Cannot determine if PDF is scanned: {', '.join(result.errors)}"
        )

    return result.is_scanned
