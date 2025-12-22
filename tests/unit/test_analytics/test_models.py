"""Tests for analytics models."""

from datetime import date
from decimal import Decimal

import pytest

from medical_bill_analyzer.analytics.models import (
    CategoryStats,
    MonthlyStats,
    PractitionerStats,
)


class TestPractitionerStats:
    """Test PractitionerStats dataclass."""

    def test_create_practitioner_stats(self):
        """Test creating PractitionerStats."""
        stats = PractitionerStats(
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_count=5,
            total_amount=Decimal("500.00"),
            average_amount=Decimal("100.00"),
            first_visit=date(2024, 1, 15),
            last_visit=date(2024, 11, 30),
        )

        assert stats.practitioner_name == "Dr. Schmidt"
        assert stats.practitioner_type == "Zahnarzt"
        assert stats.bill_count == 5
        assert stats.total_amount == Decimal("500.00")
        assert stats.average_amount == Decimal("100.00")
        assert stats.first_visit == date(2024, 1, 15)
        assert stats.last_visit == date(2024, 11, 30)

    def test_visit_span_days_calculation(self):
        """Test visit_span_days property."""
        stats = PractitionerStats(
            practitioner_name="Dr. Test",
            practitioner_type="Arzt",
            bill_count=3,
            total_amount=Decimal("300.00"),
            average_amount=Decimal("100.00"),
            first_visit=date(2024, 1, 1),
            last_visit=date(2024, 12, 31),
        )

        # 2024 is a leap year, so 366 days
        assert stats.visit_span_days == 365

    def test_visit_span_days_with_none_dates(self):
        """Test visit_span_days when dates are None."""
        stats = PractitionerStats(
            practitioner_name="Dr. Test",
            practitioner_type="Arzt",
            bill_count=1,
            total_amount=Decimal("100.00"),
            average_amount=Decimal("100.00"),
            first_visit=None,
            last_visit=None,
        )

        assert stats.visit_span_days is None

    def test_visit_span_days_with_partial_dates(self):
        """Test visit_span_days when only one date is present."""
        stats = PractitionerStats(
            practitioner_name="Dr. Test",
            practitioner_type="Arzt",
            bill_count=1,
            total_amount=Decimal("100.00"),
            average_amount=Decimal("100.00"),
            first_visit=date(2024, 1, 1),
            last_visit=None,
        )

        assert stats.visit_span_days is None

    def test_visit_span_days_same_day(self):
        """Test visit_span_days when both visits are on the same day."""
        same_date = date(2024, 6, 15)
        stats = PractitionerStats(
            practitioner_name="Dr. Test",
            practitioner_type="Arzt",
            bill_count=1,
            total_amount=Decimal("100.00"),
            average_amount=Decimal("100.00"),
            first_visit=same_date,
            last_visit=same_date,
        )

        assert stats.visit_span_days == 0

    def test_practitioner_with_none_values(self):
        """Test PractitionerStats with None name and type."""
        stats = PractitionerStats(
            practitioner_name=None,
            practitioner_type=None,
            bill_count=2,
            total_amount=Decimal("200.00"),
            average_amount=Decimal("100.00"),
            first_visit=date(2024, 1, 1),
            last_visit=date(2024, 2, 1),
        )

        assert stats.practitioner_name is None
        assert stats.practitioner_type is None
        assert stats.bill_count == 2


class TestCategoryStats:
    """Test CategoryStats dataclass."""

    def test_create_category_stats(self):
        """Test creating CategoryStats."""
        stats = CategoryStats(
            category="Zahnarzt",
            bill_count=5,
            total_amount=Decimal("500.00"),
            average_amount=Decimal("100.00"),
            percentage_of_total=Decimal("35.5"),
        )

        assert stats.category == "Zahnarzt"
        assert stats.bill_count == 5
        assert stats.total_amount == Decimal("500.00")
        assert stats.average_amount == Decimal("100.00")
        assert stats.percentage_of_total == Decimal("35.5")

    def test_is_major_category_true(self):
        """Test is_major_category property when percentage >= 20."""
        stats = CategoryStats(
            category="Zahnarzt",
            bill_count=5,
            total_amount=Decimal("500.00"),
            average_amount=Decimal("100.00"),
            percentage_of_total=Decimal("25.0"),
        )

        assert stats.is_major_category is True

    def test_is_major_category_exactly_20(self):
        """Test is_major_category at exactly 20%."""
        stats = CategoryStats(
            category="Arzt",
            bill_count=3,
            total_amount=Decimal("300.00"),
            average_amount=Decimal("100.00"),
            percentage_of_total=Decimal("20.0"),
        )

        assert stats.is_major_category is True

    def test_is_major_category_false(self):
        """Test is_major_category property when percentage < 20."""
        stats = CategoryStats(
            category="Heilpraktiker",
            bill_count=1,
            total_amount=Decimal("50.00"),
            average_amount=Decimal("50.00"),
            percentage_of_total=Decimal("5.5"),
        )

        assert stats.is_major_category is False

    def test_is_major_category_just_below_threshold(self):
        """Test is_major_category just below 20%."""
        stats = CategoryStats(
            category="Test",
            bill_count=2,
            total_amount=Decimal("150.00"),
            average_amount=Decimal("75.00"),
            percentage_of_total=Decimal("19.99"),
        )

        assert stats.is_major_category is False

    def test_category_with_zero_percentage(self):
        """Test category with 0% of total."""
        stats = CategoryStats(
            category="Unknown",
            bill_count=0,
            total_amount=Decimal("0.00"),
            average_amount=Decimal("0.00"),
            percentage_of_total=Decimal("0.0"),
        )

        assert stats.is_major_category is False
        assert stats.percentage_of_total == Decimal("0.0")


class TestMonthlyStats:
    """Test MonthlyStats dataclass."""

    def test_create_monthly_stats(self):
        """Test creating MonthlyStats."""
        stats = MonthlyStats(
            year=2024,
            month=3,
            bill_count=5,
            total_amount=Decimal("350.00"),
            average_amount=Decimal("70.00"),
        )

        assert stats.year == 2024
        assert stats.month == 3
        assert stats.bill_count == 5
        assert stats.total_amount == Decimal("350.00")
        assert stats.average_amount == Decimal("70.00")

    def test_month_name_property(self):
        """Test month_name property for various months."""
        # Test January
        stats_jan = MonthlyStats(
            year=2024,
            month=1,
            bill_count=1,
            total_amount=Decimal("100.00"),
            average_amount=Decimal("100.00"),
        )
        assert stats_jan.month_name == "Jan"

        # Test March
        stats_mar = MonthlyStats(
            year=2024,
            month=3,
            bill_count=1,
            total_amount=Decimal("100.00"),
            average_amount=Decimal("100.00"),
        )
        assert stats_mar.month_name == "Mar"

        # Test December
        stats_dec = MonthlyStats(
            year=2024,
            month=12,
            bill_count=1,
            total_amount=Decimal("100.00"),
            average_amount=Decimal("100.00"),
        )
        assert stats_dec.month_name == "Dec"

    def test_period_property(self):
        """Test period property formatting."""
        stats = MonthlyStats(
            year=2024,
            month=3,
            bill_count=5,
            total_amount=Decimal("350.00"),
            average_amount=Decimal("70.00"),
        )

        assert stats.period == "2024-03"

    def test_period_property_single_digit_month(self):
        """Test period property with single-digit month."""
        stats = MonthlyStats(
            year=2024,
            month=5,
            bill_count=2,
            total_amount=Decimal("150.00"),
            average_amount=Decimal("75.00"),
        )

        # Should be zero-padded
        assert stats.period == "2024-05"

    def test_period_property_december(self):
        """Test period property with December."""
        stats = MonthlyStats(
            year=2024,
            month=12,
            bill_count=3,
            total_amount=Decimal("250.00"),
            average_amount=Decimal("83.33"),
        )

        assert stats.period == "2024-12"

    def test_different_years(self):
        """Test stats from different years."""
        stats_2023 = MonthlyStats(
            year=2023,
            month=6,
            bill_count=2,
            total_amount=Decimal("200.00"),
            average_amount=Decimal("100.00"),
        )

        stats_2024 = MonthlyStats(
            year=2024,
            month=6,
            bill_count=3,
            total_amount=Decimal("300.00"),
            average_amount=Decimal("100.00"),
        )

        assert stats_2023.period == "2023-06"
        assert stats_2024.period == "2024-06"
        # Both June
        assert stats_2023.month_name == stats_2024.month_name == "Jun"
