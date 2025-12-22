"""Analytics result models for spending pattern analysis."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class PractitionerStats:
    """Statistics for a single practitioner.

    Attributes:
        practitioner_name: Name of the practitioner
        practitioner_type: Type/category (Arzt, Zahnarzt, etc.)
        bill_count: Number of bills/visits
        total_amount: Total spending with this practitioner
        average_amount: Average cost per visit
        first_visit: Date of first visit
        last_visit: Date of most recent visit

    Example:
        >>> stats = PractitionerStats(
        ...     practitioner_name="Dr. Schmidt",
        ...     practitioner_type="Zahnarzt",
        ...     bill_count=5,
        ...     total_amount=Decimal("500.00"),
        ...     average_amount=Decimal("100.00"),
        ...     first_visit=date(2024, 1, 15),
        ...     last_visit=date(2024, 11, 30),
        ... )
        >>> print(f"Visited {stats.bill_count} times over {stats.visit_span_days} days")
    """

    practitioner_name: Optional[str]
    practitioner_type: Optional[str]
    bill_count: int
    total_amount: Decimal
    average_amount: Decimal
    first_visit: Optional[date]
    last_visit: Optional[date]

    @property
    def visit_span_days(self) -> Optional[int]:
        """Calculate days between first and last visit.

        Returns:
            Number of days between first and last visit, or None if dates missing

        Example:
            >>> stats = PractitionerStats(..., first_visit=date(2024, 1, 1), last_visit=date(2024, 12, 31))
            >>> stats.visit_span_days
            365
        """
        if self.first_visit and self.last_visit:
            return (self.last_visit - self.first_visit).days
        return None


@dataclass
class CategoryStats:
    """Statistics for a practitioner category/type.

    Attributes:
        category: Practitioner type (Arzt, Zahnarzt, Heilpraktiker, etc.)
        bill_count: Number of bills in this category
        total_amount: Total spending in this category
        average_amount: Average cost per bill in this category
        percentage_of_total: Percentage of total spending (0-100)

    Example:
        >>> stats = CategoryStats(
        ...     category="Zahnarzt",
        ...     bill_count=12,
        ...     total_amount=Decimal("1500.00"),
        ...     average_amount=Decimal("125.00"),
        ...     percentage_of_total=Decimal("35.5"),
        ... )
        >>> if stats.is_major_category:
        ...     print(f"{stats.category} is a major expense category")
    """

    category: str
    bill_count: int
    total_amount: Decimal
    average_amount: Decimal
    percentage_of_total: Decimal

    @property
    def is_major_category(self) -> bool:
        """Check if category represents >20% of total spending.

        Returns:
            True if this category is >20% of spending

        Example:
            >>> stats = CategoryStats(..., percentage_of_total=Decimal("25.0"))
            >>> stats.is_major_category
            True
        """
        return self.percentage_of_total >= Decimal("20")


@dataclass
class MonthlyStats:
    """Statistics for a single month.

    Attributes:
        year: Year (e.g., 2024)
        month: Month number (1-12)
        bill_count: Number of bills in this month
        total_amount: Total spending in this month
        average_amount: Average cost per bill in this month

    Example:
        >>> stats = MonthlyStats(
        ...     year=2024,
        ...     month=3,
        ...     bill_count=5,
        ...     total_amount=Decimal("350.00"),
        ...     average_amount=Decimal("70.00"),
        ... )
        >>> print(f"{stats.month_name} {stats.year}: €{stats.total_amount}")
        Mar 2024: €350.00
    """

    year: int
    month: int
    bill_count: int
    total_amount: Decimal
    average_amount: Decimal

    @property
    def month_name(self) -> str:
        """Return abbreviated month name (Jan, Feb, etc.).

        Returns:
            Three-letter month abbreviation

        Example:
            >>> stats = MonthlyStats(year=2024, month=3, ...)
            >>> stats.month_name
            'Mar'
        """
        from calendar import month_abbr

        return month_abbr[self.month]

    @property
    def period(self) -> str:
        """Return formatted period (YYYY-MM).

        Returns:
            Period string in YYYY-MM format

        Example:
            >>> stats = MonthlyStats(year=2024, month=3, ...)
            >>> stats.period
            '2024-03'
        """
        return f"{self.year}-{self.month:02d}"
