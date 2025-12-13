"""PDF text extraction using pdfplumber."""

from pathlib import Path

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError

from ..core.exceptions import PDFProcessingError
from ..utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file.

    Handles multi-page PDFs by concatenating text from all pages.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text from all pages

    Raises:
        PDFProcessingError: If PDF cannot be read or processed

    Example:
        >>> text = extract_text_from_pdf(Path("bill.pdf"))
        >>> print(text[:100])
    """
    if not pdf_path.exists():
        raise PDFProcessingError(f"PDF file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise PDFProcessingError(f"Path is not a file: {pdf_path}")

    try:
        logger.info(f"Extracting text from PDF: {pdf_path}")

        with pdfplumber.open(pdf_path) as pdf:
            # Check if PDF has pages
            if not pdf.pages:
                raise PDFProcessingError(f"PDF has no pages: {pdf_path}")

            # Extract text from all pages
            text_parts = []
            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()

                if page_text:
                    text_parts.append(page_text)
                    logger.debug(f"Extracted {len(page_text)} characters from page {i}")
                else:
                    logger.warning(f"No text found on page {i}")

            # Concatenate all pages with newlines
            full_text = "\n\n".join(text_parts)

            if not full_text.strip():
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                return ""

            logger.info(
                f"Successfully extracted {len(full_text)} characters "
                f"from {len(pdf.pages)} page(s)"
            )

            return full_text

    except PDFSyntaxError as e:
        raise PDFProcessingError(
            f"PDF appears to be corrupted or malformed: {e}"
        ) from e

    except PDFPasswordIncorrect as e:
        raise PDFProcessingError(
            f"PDF is password-protected and cannot be read: {pdf_path}"
        ) from e

    except Exception as e:
        raise PDFProcessingError(
            f"Failed to extract text from PDF {pdf_path}: {e}"
        ) from e
