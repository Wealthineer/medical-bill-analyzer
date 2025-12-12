"""Currency utility functions for handling EUR amounts."""

from decimal import Decimal, InvalidOperation
from typing import Optional
import re

from .logger import get_logger

logger = get_logger(__name__)


def format_euro(amount: Decimal | float, include_symbol: bool = True) -> str:
    """
    Format an amount as EUR currency.

    German format: 1.234,56 €

    Args:
        amount: Amount to format
        include_symbol: Whether to include € symbol (default: True)

    Returns:
        str: Formatted currency string
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))

    # Format with German locale (dot as thousands separator, comma as decimal)
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if include_symbol:
        return f"€{formatted}"
    return formatted


def parse_euro(amount_string: str) -> Optional[Decimal]:
    """
    Parse a EUR currency string to Decimal.

    Handles various formats:
    - 1.234,56 € (German format)
    - €1.234,56
    - 1234.56 (English format)
    - 1.234,56
    - 1,234.56

    Args:
        amount_string: Currency string to parse

    Returns:
        Decimal or None if parsing fails
    """
    if not amount_string:
        return None

    # Remove whitespace and currency symbols
    cleaned = amount_string.strip().replace("€", "").replace("EUR", "").strip()

    # Detect format based on last separator
    # German: 1.234,56 (comma is decimal separator)
    # English: 1,234.56 (dot is decimal separator)

    # Count dots and commas
    dot_count = cleaned.count(".")
    comma_count = cleaned.count(",")

    try:
        if comma_count > 0 and dot_count == 0:
            # Only comma: could be German decimal (12,50) or English thousands (1,234)
            if comma_count == 1:
                # Single comma: likely German decimal separator
                cleaned = cleaned.replace(",", ".")
            else:
                # Multiple commas: English thousands separator
                cleaned = cleaned.replace(",", "")

        elif dot_count > 0 and comma_count == 0:
            # Only dots: could be German thousands (1.234) or English decimal (12.50)
            if dot_count == 1:
                # Single dot: likely English decimal separator
                pass  # Already in correct format
            else:
                # Multiple dots: German thousands separator
                cleaned = cleaned.replace(".", "")

        elif dot_count > 0 and comma_count > 0:
            # Both present: determine which is decimal separator by position
            last_dot_pos = cleaned.rfind(".")
            last_comma_pos = cleaned.rfind(",")

            if last_comma_pos > last_dot_pos:
                # German format: 1.234,56
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # English format: 1,234.56
                cleaned = cleaned.replace(",", "")

        return Decimal(cleaned)

    except (InvalidOperation, ValueError) as e:
        logger.warning(f"Failed to parse amount '{amount_string}': {e}")
        return None


def is_valid_amount(amount: Decimal | float) -> bool:
    """
    Check if an amount is valid (positive and not zero).

    Args:
        amount: Amount to check

    Returns:
        bool: True if amount is valid
    """
    if isinstance(amount, float):
        amount = Decimal(str(amount))

    return amount > 0
