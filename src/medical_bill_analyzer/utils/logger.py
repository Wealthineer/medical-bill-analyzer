"""Logging configuration for Medical Bill Analyzer."""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..config.defaults import get_user_logs_dir


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True,
) -> None:
    """
    Set up logging configuration.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional path to log file. If None, uses default location.
        console: Whether to also log to console (default: True)
    """
    # Create logs directory
    logs_dir = get_user_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Use default log file if not specified
    if log_file is None:
        log_file = logs_dir / "medical_bill_analyzer.log"

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(
        "%(levelname)s: %(message)s"
    )

    # Create handlers
    handlers = []

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
