"""File utility functions."""

import hashlib
import re
import shutil
from pathlib import Path
from typing import Optional

from ..core.exceptions import PDFProcessingError
from .logger import get_logger

logger = get_logger(__name__)


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        str: Hexadecimal hash string

    Raises:
        PDFProcessingError: If file cannot be read
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks for memory efficiency
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise PDFProcessingError(f"Failed to calculate hash for {file_path}: {e}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    # Keep alphanumeric, dots, hyphens, underscores
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"

    # Limit length to 255 characters (common filesystem limit)
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_length = 255 - len(ext) - 1
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:255]

    return filename


def copy_file_to_storage(
    source_path: Path,
    storage_dir: Path,
    new_filename: Optional[str] = None,
) -> Path:
    """
    Copy a file to the storage directory.

    Args:
        source_path: Source file path
        storage_dir: Destination storage directory
        new_filename: Optional new filename (if None, uses original sanitized name)

    Returns:
        Path: Path to the copied file

    Raises:
        PDFProcessingError: If copy operation fails
    """
    try:
        # Create storage directory if it doesn't exist
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Determine destination filename
        if new_filename is None:
            new_filename = source_path.name

        # Sanitize filename
        safe_filename = sanitize_filename(new_filename)

        # Create destination path
        dest_path = storage_dir / safe_filename

        # Handle filename conflicts by appending number
        if dest_path.exists():
            base_name = dest_path.stem
            extension = dest_path.suffix
            counter = 1
            while dest_path.exists():
                safe_filename = f"{base_name}_{counter}{extension}"
                dest_path = storage_dir / safe_filename
                counter += 1

        # Copy file
        shutil.copy2(source_path, dest_path)
        logger.debug(f"Copied file from {source_path} to {dest_path}")

        return dest_path

    except Exception as e:
        raise PDFProcessingError(f"Failed to copy file to storage: {e}")


def ensure_directory_exists(directory: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path
    """
    directory.mkdir(parents=True, exist_ok=True)
