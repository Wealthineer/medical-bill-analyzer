"""Tests for bonus calculator."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from medical_bill_analyzer.core.bonus_calculator import (
    BonusCalculator,
    BonusRecommendation,
)
from medical_bill_analyzer.database.models import BillFilter


@pytest.fixture
def mock_repository():
    """Create mock BillRepository."""
    repository = Mock()
    return repository


@pytest.fixture
def calculator(mock_repository):
    """Create BonusCalculator with mock repository."""
    return BonusCalculator(mock_repository)


class TestBonusRecommendation:
    """Test BonusRecommendation dataclass."""

    def test_create_keep_bonus_recommendation(self):
        """Test creating keep_bonus recommendation."""
        rec = BonusRecommendation(
            total_amount=Decimal("800"),
            bonus_threshold=Decimal("1000"),
            recommendation="keep_bonus",
            savings=Decimal("200"),
            difference=Decimal("-200"),
            explanation="Keep bonus - save €200",
        )

        assert rec.total_amount == Decimal("800")
        assert rec.bonus_threshold == Decimal("1000")
        assert rec.recommendation == "keep_bonus"
        assert rec.savings == Decimal("200")
        assert rec.difference == Decimal("-200")

    def test_should_keep_bonus_property(self):
        """Test should_keep_bonus property."""
        rec = BonusRecommendation(
            total_amount=Decimal("800"),
            bonus_threshold=Decimal("1000"),
            recommendation="keep_bonus",
            savings=Decimal("200"),
            difference=Decimal("-200"),
            explanation="",
        )
        assert rec.should_keep_bonus is True
        assert rec.should_submit_claims is False

    def test_should_submit_claims_property(self):
        """Test should_submit_claims property."""
        rec = BonusRecommendation(
            total_amount=Decimal("1200"),
            bonus_threshold=Decimal("1000"),
            recommendation="submit_claims",
            savings=Decimal("200"),
            difference=Decimal("200"),
            explanation="",
        )
        assert rec.should_keep_bonus is False
        assert rec.should_submit_claims is True


class TestBonusCalculatorInit:
    """Test BonusCalculator initialization."""

    def test_initialization(self, mock_repository):
        """Test calculator initializes correctly."""
        calculator = BonusCalculator(mock_repository)
        assert calculator.repository == mock_repository


class TestCalculateTotal:
    """Test calculate_total method."""

    def test_calculate_total_by_year(self, calculator, mock_repository):
        """Test calculating total for a year."""
        mock_repository.get_total_amount.return_value = Decimal("1234.56")

        total = calculator.calculate_total(year=2024)

        assert total == Decimal("1234.56")
        # Should call with BillFilter(year=2024)
        call_args = mock_repository.get_total_amount.call_args[0][0]
        assert isinstance(call_args, BillFilter)
        assert call_args.year == 2024

    def test_calculate_total_by_date_range(self, calculator, mock_repository):
        """Test calculating total for date range."""
        from_date = date(2024, 1, 1)
        to_date = date(2024, 12, 31)
        mock_repository.get_total_amount.return_value = Decimal("555.55")

        total = calculator.calculate_total(from_date=from_date, to_date=to_date)

        assert total == Decimal("555.55")
        # Should call with BillFilter(start_date=from_date, end_date=to_date)
        call_args = mock_repository.get_total_amount.call_args[0][0]
        assert isinstance(call_args, BillFilter)
        assert call_args.start_date == from_date
        assert call_args.end_date == to_date

    def test_calculate_total_with_filter(self, calculator, mock_repository):
        """Test calculating total with custom filter."""
        bill_filter = BillFilter(practitioner_type="Zahnarzt", year=2024)
        mock_repository.get_total_amount.return_value = Decimal("300.00")

        total = calculator.calculate_total(filter_obj=bill_filter)

        assert total == Decimal("300.00")
        mock_repository.get_total_amount.assert_called_once_with(bill_filter)

    def test_calculate_total_no_filter(self, calculator, mock_repository):
        """Test calculating total without any filter."""
        mock_repository.get_total_amount.return_value = Decimal("999.99")

        total = calculator.calculate_total()

        assert total == Decimal("999.99")
        # Should call with empty filter
        call_args = mock_repository.get_total_amount.call_args[0][0]
        assert isinstance(call_args, BillFilter)


class TestCompareToThreshold:
    """Test compare_to_threshold method."""

    def test_costs_below_threshold(self, calculator):
        """Test when costs are below threshold - keep bonus."""
        rec = calculator.compare_to_threshold(
            total=Decimal("800"),
            threshold=Decimal("1000"),
        )

        assert rec.total_amount == Decimal("800")
        assert rec.bonus_threshold == Decimal("1000")
        assert rec.recommendation == "keep_bonus"
        assert rec.savings == Decimal("200")
        assert rec.difference == Decimal("-200")
        assert "Keep your bonus" in rec.explanation
        assert "€200" in rec.explanation
        assert rec.should_keep_bonus is True

    def test_costs_above_threshold(self, calculator):
        """Test when costs exceed threshold - submit claims."""
        rec = calculator.compare_to_threshold(
            total=Decimal("1500"),
            threshold=Decimal("1000"),
        )

        assert rec.total_amount == Decimal("1500")
        assert rec.bonus_threshold == Decimal("1000")
        assert rec.recommendation == "submit_claims"
        assert rec.savings == Decimal("500")
        assert rec.difference == Decimal("500")
        assert "Submit your claims" in rec.explanation
        assert "€500" in rec.explanation
        assert rec.should_submit_claims is True

    def test_costs_equal_threshold(self, calculator):
        """Test when costs equal threshold - neutral (prefer keep)."""
        rec = calculator.compare_to_threshold(
            total=Decimal("1000"),
            threshold=Decimal("1000"),
        )

        assert rec.total_amount == Decimal("1000")
        assert rec.bonus_threshold == Decimal("1000")
        assert rec.recommendation == "keep_bonus"  # Prefer keeping
        assert rec.savings == Decimal("0")
        assert rec.difference == Decimal("0")
        assert "exactly at your threshold" in rec.explanation
        assert rec.should_keep_bonus is True

    def test_with_float_inputs(self, calculator):
        """Test that floats are converted to Decimal."""
        rec = calculator.compare_to_threshold(
            total=850.50,
            threshold=1000.00,
        )

        # Should work and convert to Decimal
        assert isinstance(rec.total_amount, Decimal)
        assert isinstance(rec.bonus_threshold, Decimal)
        assert rec.recommendation == "keep_bonus"

    def test_small_difference_below(self, calculator):
        """Test with small difference below threshold."""
        rec = calculator.compare_to_threshold(
            total=Decimal("999.99"),
            threshold=Decimal("1000.00"),
        )

        assert rec.recommendation == "keep_bonus"
        assert rec.savings == Decimal("0.01")

    def test_small_difference_above(self, calculator):
        """Test with small difference above threshold."""
        rec = calculator.compare_to_threshold(
            total=Decimal("1000.01"),
            threshold=Decimal("1000.00"),
        )

        assert rec.recommendation == "submit_claims"
        assert rec.savings == Decimal("0.01")

    def test_large_difference_below(self, calculator):
        """Test with large difference below threshold."""
        rec = calculator.compare_to_threshold(
            total=Decimal("100"),
            threshold=Decimal("1000"),
        )

        assert rec.recommendation == "keep_bonus"
        assert rec.savings == Decimal("900")
        assert rec.difference == Decimal("-900")

    def test_large_difference_above(self, calculator):
        """Test with large difference above threshold."""
        rec = calculator.compare_to_threshold(
            total=Decimal("5000"),
            threshold=Decimal("1000"),
        )

        assert rec.recommendation == "submit_claims"
        assert rec.savings == Decimal("4000")
        assert rec.difference == Decimal("4000")

    def test_zero_threshold(self, calculator):
        """Test with zero threshold (always submit)."""
        rec = calculator.compare_to_threshold(
            total=Decimal("100"),
            threshold=Decimal("0"),
        )

        assert rec.recommendation == "submit_claims"
        assert rec.savings == Decimal("100")

    def test_zero_costs(self, calculator):
        """Test with zero costs (always keep)."""
        rec = calculator.compare_to_threshold(
            total=Decimal("0"),
            threshold=Decimal("1000"),
        )

        assert rec.recommendation == "keep_bonus"
        assert rec.savings == Decimal("1000")


class TestGetRecommendationForYear:
    """Test get_recommendation_for_year convenience method."""

    def test_get_recommendation_for_year(self, calculator, mock_repository):
        """Test getting recommendation for a year."""
        mock_repository.get_total_amount.return_value = Decimal("750")

        rec = calculator.get_recommendation_for_year(2024, Decimal("1000"))

        assert rec.recommendation == "keep_bonus"
        assert rec.total_amount == Decimal("750")
        assert rec.bonus_threshold == Decimal("1000")
        assert rec.savings == Decimal("250")
        # Should call with BillFilter(year=2024)
        call_args = mock_repository.get_total_amount.call_args[0][0]
        assert isinstance(call_args, BillFilter)
        assert call_args.year == 2024

    def test_get_recommendation_combines_methods(self, calculator, mock_repository):
        """Test that get_recommendation_for_year combines calculate_total and compare_to_threshold."""
        mock_repository.get_total_amount.return_value = Decimal("1500")

        rec = calculator.get_recommendation_for_year(2024, Decimal("1000"))

        # Should calculate total for year with BillFilter
        call_args = mock_repository.get_total_amount.call_args[0][0]
        assert isinstance(call_args, BillFilter)
        assert call_args.year == 2024
        # Should return recommendation based on comparison
        assert rec.recommendation == "submit_claims"
        assert rec.total_amount == Decimal("1500")
        assert rec.savings == Decimal("500")
