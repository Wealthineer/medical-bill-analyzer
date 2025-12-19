"""Shared utilities for CLI commands."""

from pathlib import Path
from typing import Optional

import typer

from medical_bill_analyzer.config.settings import Settings, get_settings
from medical_bill_analyzer.core.exceptions import ConfigError
from medical_bill_analyzer.database.connection import DatabaseConnection
from medical_bill_analyzer.utils.logger import get_logger

logger = get_logger(__name__)


def load_config() -> Settings:
    """Load configuration file.

    Returns:
        Settings object

    Raises:
        typer.Exit: If config not found
    """
    try:
        settings = get_settings()
        return settings
    except (ConfigError, FileNotFoundError) as e:
        typer.secho(
            f"\n❌ Configuration error: {e}",
            fg=typer.colors.RED,
            err=True,
        )
        typer.secho(
            "\n💡 Run 'medical-bill-analyzer setup' to configure the application",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)


def get_database_path(settings: Optional[Settings] = None) -> Path:
    """Get database path from settings.

    Args:
        settings: Optional settings object (loads if not provided)

    Returns:
        Path to database file
    """
    if settings is None:
        settings = load_config()

    return Path(settings.storage.database_path).expanduser()


def get_credential_repository(settings: Optional[Settings] = None):
    """Get credential repository.

    Args:
        settings: Optional settings object (loads if not provided)

    Returns:
        CredentialRepository instance
    """
    from medical_bill_analyzer.database.repositories import CredentialRepository

    db_path = get_database_path(settings)
    return CredentialRepository(db_path)


def format_currency(amount: float) -> str:
    """Format amount as EUR currency.

    Args:
        amount: Amount to format

    Returns:
        Formatted string (e.g., "€1,234.56")
    """
    return f"€{amount:,.2f}"


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation.

    Args:
        message: Confirmation message
        default: Default value if user just presses Enter

    Returns:
        True if user confirms, False otherwise
    """
    return typer.confirm(message, default=default)


def success_message(message: str):
    """Print success message in green.

    Args:
        message: Message to print
    """
    typer.secho(f"✓ {message}", fg=typer.colors.GREEN)


def error_message(message: str):
    """Print error message in red.

    Args:
        message: Message to print
    """
    typer.secho(f"✗ {message}", fg=typer.colors.RED, err=True)


def info_message(message: str):
    """Print info message in blue.

    Args:
        message: Message to print
    """
    typer.secho(f"ℹ {message}", fg=typer.colors.BLUE)


def warning_message(message: str):
    """Print warning message in yellow.

    Args:
        message: Message to print
    """
    typer.secho(f"⚠ {message}", fg=typer.colors.YELLOW)
