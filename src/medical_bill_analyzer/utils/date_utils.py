"""Date utility functions for handling German date formats."""

from datetime import date, datetime
from typing import Optional
from dateutil import parser
import re

from ..core.exceptions import ValidationError
from .logger import get_logger

logger = get_logger(__name__)


def parse_german_date(date_string: str) -> Optional[date]:
    """
    Parse a German date string into a date object.

    Handles common German formats:
    - DD.MM.YYYY (e.g., 25.12.2024)
    - DD.MM.YY (e.g., 25.12.24)
    - DD/MM/YYYY
    - YYYY-MM-DD (ISO format)

    Args:
        date_string: Date string to parse

    Returns:
        date object or None if parsing fails
    """
    if not date_string:
        return None

    date_string = date_string.strip()

    # Try common German format (DD.MM.YYYY)
    german_pattern = r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})"
    match = re.match(german_pattern, date_string)
    if match:
        try:
            day, month, year = match.groups()
            day = int(day)
            month = int(month)
            year = int(year)

            # Handle 2-digit years
            if year < 100:
                # Assume 20xx for years 00-50, 19xx for 51-99
                year = 2000 + year if year <= 50 else 1900 + year

            return date(year, month, day)
        except ValueError as e:
            logger.warning(f"Invalid date values in {date_string}: {e}")
            return None

    # Try dateutil parser as fallback (handles many formats)
    try:
        parsed = parser.parse(date_string, dayfirst=True)
        return parsed.date()
    except (ValueError, parser.ParserError) as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None


def format_date(d: date, format_str: str = "%d.%m.%Y") -> str:
    """
    Format a date object as a string.

    Args:
        d: Date object
        format_str: Format string (default: German format DD.MM.YYYY)

    Returns:
        str: Formatted date string
    """
    return d.strftime(format_str)


def is_date_in_past(d: date) -> bool:
    """
    Check if a date is in the past.

    Args:
        d: Date to check

    Returns:
        bool: True if date is in the past, False otherwise
    """
    return d < date.today()


def is_date_in_future(d: date) -> bool:
    """
    Check if a date is in the future.

    Args:
        d: Date to check

    Returns:
        bool: True if date is in the future, False otherwise
    """
    return d > date.today()


def get_date_range_for_year(year: int) -> tuple[date, date]:
    """
    Get the date range (start, end) for a given year.

    Args:
        year: Year

    Returns:
        tuple: (start_date, end_date) for the year
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    return start_date, end_date
