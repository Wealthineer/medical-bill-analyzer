"""Data validation utility functions."""

from datetime import date
from decimal import Decimal
from typing import Optional

from ..core.exceptions import ValidationError

# Valid practitioner types
VALID_PRACTITIONER_TYPES = {
    "Arzt",
    "Zahnarzt",
    "Heilpraktiker",
    "Krankenhaus",
    "Labor",
    "Apotheke",
    "Sonstige",
}


def validate_amount(amount: Optional[Decimal | float], allow_zero: bool = False) -> bool:
    """
    Validate that an amount is positive (and optionally non-zero).

    Args:
        amount: Amount to validate
        allow_zero: Whether to allow zero values (default: False)

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If amount is invalid
    """
    if amount is None:
        return False

    if isinstance(amount, float):
        amount = Decimal(str(amount))

    if allow_zero:
        if amount < 0:
            raise ValidationError(f"Amount must be non-negative, got {amount}")
    else:
        if amount <= 0:
            raise ValidationError(f"Amount must be positive, got {amount}")

    return True


def validate_date(
    d: Optional[date],
    require_past: bool = True,
    allow_future: bool = False,
) -> bool:
    """
    Validate a date.

    Args:
        d: Date to validate
        require_past: Require date to be in the past (default: True)
        allow_future: Allow future dates (default: False)

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If date is invalid
    """
    if d is None:
        return False

    if require_past and d >= date.today():
        raise ValidationError(f"Date must be in the past, got {d}")

    if not allow_future and d > date.today():
        raise ValidationError(f"Future dates not allowed, got {d}")

    return True


def validate_practitioner_type(practitioner_type: Optional[str]) -> bool:
    """
    Validate that a practitioner type is one of the allowed values.

    Args:
        practitioner_type: Type to validate

    Returns:
        bool: True if valid

    Raises:
        ValidationError: If type is invalid
    """
    if practitioner_type is None:
        return False

    if practitioner_type not in VALID_PRACTITIONER_TYPES:
        raise ValidationError(
            f"Invalid practitioner type '{practitioner_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_PRACTITIONER_TYPES))}"
        )

    return True
