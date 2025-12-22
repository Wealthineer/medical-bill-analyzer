"""Bonus calculator - calculates totals and bonus recommendations."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from ..database.models import BillFilter
from ..database.repositories.bill_repository import BillRepository
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BonusRecommendation:
    """Bonus vs. claim submission recommendation.

    Attributes:
        total_amount: Total medical costs for the period
        bonus_threshold: Annual bonus amount at risk
        recommendation: "keep_bonus" or "submit_claims"
        savings: How much money would be saved by following recommendation
        difference: Difference between total and threshold (positive = over threshold)
        explanation: Human-readable explanation

    Example:
        >>> rec = BonusRecommendation(
        ...     total_amount=Decimal("800"),
        ...     bonus_threshold=Decimal("1000"),
        ...     recommendation="keep_bonus",
        ...     savings=Decimal("200"),
        ...     difference=Decimal("-200"),
        ...     explanation="Keep bonus - costs are €200 below threshold"
        ... )
    """

    total_amount: Decimal
    bonus_threshold: Decimal
    recommendation: str  # "keep_bonus" or "submit_claims"
    savings: Decimal
    difference: Decimal
    explanation: str

    @property
    def should_keep_bonus(self) -> bool:
        """Check if recommendation is to keep bonus."""
        return self.recommendation == "keep_bonus"

    @property
    def should_submit_claims(self) -> bool:
        """Check if recommendation is to submit claims."""
        return self.recommendation == "submit_claims"


class BonusCalculator:
    """Calculates medical costs and bonus recommendations.

    German private health insurance (PKV) typically offers an annual bonus
    for not submitting claims. This calculator helps decide whether to
    keep the bonus or submit claims for reimbursement.

    Decision logic:
    - If total costs < bonus threshold: Keep bonus (save the difference)
    - If total costs > bonus threshold: Submit claims (save the difference)
    - If total costs = bonus threshold: Neutral (slight preference for keeping bonus)

    Example:
        >>> from medical_bill_analyzer.database.repositories import BillRepository
        >>> repository = BillRepository(connection)
        >>> calculator = BonusCalculator(repository)
        >>>
        >>> # Calculate total for 2024
        >>> total = calculator.calculate_total(year=2024)
        >>> print(f"Total costs 2024: €{total}")
        >>>
        >>> # Get recommendation
        >>> rec = calculator.compare_to_threshold(
        ...     total=total,
        ...     threshold=Decimal("1000")
        ... )
        >>> print(rec.explanation)
    """

    def __init__(self, repository: BillRepository):
        """Initialize bonus calculator.

        Args:
            repository: BillRepository for querying bills
        """
        self.repository = repository
        logger.info("Initialized BonusCalculator")

    def calculate_total(
        self,
        year: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        filter_obj: Optional[BillFilter] = None,
    ) -> Decimal:
        """Calculate total medical costs.

        Args:
            year: Optional year to filter by
            from_date: Optional start date
            to_date: Optional end date
            filter_obj: Optional BillFilter for advanced filtering

        Returns:
            Total amount as Decimal

        Example:
            >>> # Total for current year
            >>> total = calculator.calculate_total(year=2024)
            >>>
            >>> # Total for date range
            >>> total = calculator.calculate_total(
            ...     from_date=date(2024, 1, 1),
            ...     to_date=date(2024, 12, 31)
            ... )
            >>>
            >>> # Total with custom filter
            >>> filter_obj = BillFilter(
            ...     practitioner_type="Zahnarzt",
            ...     year=2024
            ... )
            >>> total = calculator.calculate_total(filter_obj=filter_obj)
        """
        logger.info(f"Calculating total (year={year}, from={from_date}, to={to_date})")

        if filter_obj:
            # Use provided filter
            total = self.repository.get_total_amount(filter_obj)
        elif year:
            # Filter by year
            total = self.repository.get_total_amount(BillFilter(year=year))
        elif from_date and to_date:
            # Filter by date range
            total = self.repository.get_total_amount(
                BillFilter(start_date=from_date, end_date=to_date)
            )
        else:
            # No filter - get all bills
            total = self.repository.get_total_amount(BillFilter())

        logger.info(f"Calculated total: €{total}")
        return total

    def compare_to_threshold(
        self, total: Decimal, threshold: Decimal
    ) -> BonusRecommendation:
        """Compare total costs to bonus threshold.

        Args:
            total: Total medical costs
            threshold: Annual bonus amount

        Returns:
            BonusRecommendation with decision and explanation

        Example:
            >>> rec = calculator.compare_to_threshold(
            ...     total=Decimal("800"),
            ...     threshold=Decimal("1000")
            ... )
            >>> print(rec.recommendation)  # "keep_bonus"
            >>> print(f"Save €{rec.savings}")  # "Save €200"
        """
        logger.info(f"Comparing total €{total} to threshold €{threshold}")

        # Convert to Decimal if needed
        if not isinstance(total, Decimal):
            total = Decimal(str(total))
        if not isinstance(threshold, Decimal):
            threshold = Decimal(str(threshold))

        # Calculate difference (positive = costs exceed threshold)
        difference = total - threshold

        if difference < 0:
            # Costs are below threshold - keep bonus
            savings = abs(difference)
            recommendation = "keep_bonus"
            explanation = (
                f"💰 Keep your bonus! Your medical costs (€{total:.2f}) are "
                f"€{savings:.2f} below your bonus threshold (€{threshold:.2f}). "
                f"By not submitting claims, you save €{savings:.2f}."
            )
            logger.info(f"Recommendation: Keep bonus (save €{savings})")

        elif difference > 0:
            # Costs exceed threshold - submit claims
            savings = difference
            recommendation = "submit_claims"
            explanation = (
                f"📋 Submit your claims! Your medical costs (€{total:.2f}) exceed "
                f"your bonus threshold (€{threshold:.2f}) by €{savings:.2f}. "
                f"By submitting claims, you save €{savings:.2f}."
            )
            logger.info(f"Recommendation: Submit claims (save €{savings})")

        else:
            # Exactly at threshold - neutral but prefer keeping bonus
            savings = Decimal("0")
            recommendation = "keep_bonus"
            explanation = (
                f"⚖️  You're exactly at your threshold! Your medical costs "
                f"(€{total:.2f}) equal your bonus (€{threshold:.2f}). "
                f"Either option works, but keeping the bonus avoids paperwork."
            )
            logger.info("Recommendation: Neutral (at threshold)")

        return BonusRecommendation(
            total_amount=total,
            bonus_threshold=threshold,
            recommendation=recommendation,
            savings=savings,
            difference=difference,
            explanation=explanation,
        )

    def get_recommendation_for_year(
        self, year: int, threshold: Decimal
    ) -> BonusRecommendation:
        """Get bonus recommendation for a specific year.

        Convenience method that combines calculate_total() and compare_to_threshold().

        Args:
            year: Year to calculate for
            threshold: Bonus threshold amount

        Returns:
            BonusRecommendation

        Example:
            >>> rec = calculator.get_recommendation_for_year(2024, Decimal("1000"))
            >>> print(rec.explanation)
        """
        total = self.calculate_total(year=year)
        return self.compare_to_threshold(total, threshold)
