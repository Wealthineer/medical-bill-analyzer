"""Analytics engine for medical bill spending pattern analysis."""

from decimal import Decimal
from typing import List, Optional

from ..database.models import BillFilter
from ..database.repositories.bill_repository import BillRepository
from ..utils.logger import get_logger
from .models import CategoryStats, MonthlyStats, PractitionerStats

logger = get_logger(__name__)


class AnalyticsEngine:
    """Analytics engine for medical bill spending patterns.

    Analyzes bills to provide insights by practitioner, category, and time.
    Similar to BonusCalculator but focused on analytics/reporting.

    Example:
        >>> from medical_bill_analyzer.database.repositories import BillRepository
        >>> repository = BillRepository(db_path)
        >>> engine = AnalyticsEngine(repository)
        >>>
        >>> # Get top 10 practitioners by spending
        >>> stats = engine.get_practitioner_stats(limit=10)
        >>> for stat in stats:
        ...     print(f"{stat.practitioner_name}: €{stat.total_amount}")
        >>>
        >>> # Get category breakdown for 2024
        >>> filter_obj = BillFilter(year=2024)
        >>> categories = engine.get_category_stats(filter_obj)
        >>> for cat in categories:
        ...     print(f"{cat.category}: {cat.percentage_of_total:.1f}%")
    """

    def __init__(self, repository: BillRepository):
        """Initialize analytics engine.

        Args:
            repository: BillRepository for data access
        """
        self.repository = repository
        logger.info("Initialized AnalyticsEngine")

    def get_practitioner_stats(
        self,
        filter_obj: Optional[BillFilter] = None,
        limit: Optional[int] = None,
    ) -> List[PractitionerStats]:
        """Get spending statistics grouped by practitioner.

        Args:
            filter_obj: Optional filter (year, date range, type)
            limit: Optional limit for top N practitioners

        Returns:
            List of PractitionerStats, sorted by total_amount descending

        Example:
            >>> # Get all practitioners for 2024
            >>> filter_obj = BillFilter(year=2024)
            >>> stats = engine.get_practitioner_stats(filter_obj)
            >>>
            >>> # Get top 5 practitioners
            >>> stats = engine.get_practitioner_stats(limit=5)
        """
        logger.info(f"Calculating practitioner stats (limit={limit})")

        # Get raw data from repository
        raw_stats = self.repository.get_practitioner_stats(filter_obj)

        # Convert to domain models
        results = [
            PractitionerStats(
                practitioner_name=row["practitioner_name"],
                practitioner_type=row["practitioner_type"],
                bill_count=row["bill_count"],
                total_amount=row["total_amount"],
                average_amount=row["average_amount"],
                first_visit=row["first_visit"],
                last_visit=row["last_visit"],
            )
            for row in raw_stats
        ]

        # Apply limit if specified
        if limit:
            results = results[:limit]

        logger.info(f"Found {len(results)} practitioners")
        return results

    def get_category_stats(
        self,
        filter_obj: Optional[BillFilter] = None,
    ) -> List[CategoryStats]:
        """Get spending statistics grouped by category/type.

        Args:
            filter_obj: Optional filter (year, date range)

        Returns:
            List of CategoryStats with percentages, sorted by total_amount descending

        Example:
            >>> # Get category breakdown for all time
            >>> stats = engine.get_category_stats()
            >>>
            >>> # Get category breakdown for 2024
            >>> filter_obj = BillFilter(year=2024)
            >>> stats = engine.get_category_stats(filter_obj)
            >>> for stat in stats:
            ...     if stat.is_major_category:
            ...         print(f"Major category: {stat.category}")
        """
        logger.info("Calculating category stats")

        raw_stats = self.repository.get_category_stats(filter_obj)

        # Calculate total for percentages
        total_spending = sum(row["total_amount"] for row in raw_stats)

        # Convert to domain models with percentages
        results = [
            CategoryStats(
                category=row["category"],
                bill_count=row["bill_count"],
                total_amount=row["total_amount"],
                average_amount=row["average_amount"],
                percentage_of_total=(
                    (row["total_amount"] / total_spending * 100)
                    if total_spending > 0
                    else Decimal("0")
                ),
            )
            for row in raw_stats
        ]

        logger.info(f"Found {len(results)} categories")
        return results

    def get_monthly_stats(
        self,
        filter_obj: Optional[BillFilter] = None,
    ) -> List[MonthlyStats]:
        """Get spending statistics grouped by month.

        Args:
            filter_obj: Optional filter (year, date range, type)

        Returns:
            List of MonthlyStats, sorted by year and month

        Example:
            >>> # Get monthly breakdown for 2024
            >>> filter_obj = BillFilter(year=2024)
            >>> stats = engine.get_monthly_stats(filter_obj)
            >>> for stat in stats:
            ...     print(f"{stat.period}: €{stat.total_amount} ({stat.bill_count} bills)")
        """
        logger.info("Calculating monthly stats")

        raw_stats = self.repository.get_monthly_stats(filter_obj)

        # Convert to domain models
        results = [
            MonthlyStats(
                year=row["year"],
                month=row["month"],
                bill_count=row["bill_count"],
                total_amount=row["total_amount"],
                average_amount=row["average_amount"],
            )
            for row in raw_stats
        ]

        logger.info(f"Found {len(results)} months")
        return results
