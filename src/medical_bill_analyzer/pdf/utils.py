"""PDF utility functions."""

from pathlib import Path

from ..utils.file_utils import calculate_file_hash
from ..utils.logger import get_logger

logger = get_logger(__name__)


def get_pdf_hash(pdf_path: Path) -> str:
    """
    Calculate SHA256 hash of a PDF file.

    This is a convenience wrapper around calculate_file_hash
    specifically for PDFs.

    Args:
        pdf_path: Path to PDF file

    Returns:
        SHA256 hash as hexadecimal string

    Example:
        >>> hash1 = get_pdf_hash(Path("bill.pdf"))
        >>> hash2 = get_pdf_hash(Path("bill_copy.pdf"))
        >>> if hash1 == hash2:
        ...     print("These are identical files")
    """
    return calculate_file_hash(pdf_path)


def get_pdf_info(pdf_path: Path) -> dict:
    """
    Get basic information about a PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dictionary with PDF information:
        - filename: Original filename
        - size_bytes: File size in bytes
        - size_mb: File size in megabytes
        - hash: SHA256 hash

    Example:
        >>> info = get_pdf_info(Path("bill.pdf"))
        >>> print(f"Size: {info['size_mb']:.2f} MB")
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    size_bytes = pdf_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    return {
        "filename": pdf_path.name,
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "hash": get_pdf_hash(pdf_path),
    }
