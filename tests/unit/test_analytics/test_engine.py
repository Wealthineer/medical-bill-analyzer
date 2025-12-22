"""Tests for AnalyticsEngine."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from medical_bill_analyzer.analytics.engine import AnalyticsEngine
from medical_bill_analyzer.analytics.models import (
    CategoryStats,
    MonthlyStats,
    PractitionerStats,
)
from medical_bill_analyzer.database.models import BillFilter


class TestAnalyticsEngineInit:
    """Test AnalyticsEngine initialization."""

    def test_initialization(self, mock_repository):
        """Test engine initializes correctly."""
        engine = AnalyticsEngine(mock_repository)
        assert engine.repository == mock_repository


class TestGetPractitionerStats:
    """Test get_practitioner_stats method."""

    def test_get_practitioner_stats_no_filter(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test getting practitioner stats without filter."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data

        stats = analytics_engine.get_practitioner_stats()

        assert len(stats) == 3
        mock_repository.get_practitioner_stats.assert_called_once_with(None)

        # Verify first practitioner
        assert stats[0].practitioner_name == "Dr. Schmidt"
        assert stats[0].practitioner_type == "Zahnarzt"
        assert stats[0].bill_count == 5
        assert stats[0].total_amount == Decimal("500.00")
        assert stats[0].average_amount == Decimal("100.00")
        assert stats[0].first_visit == date(2024, 1, 15)
        assert stats[0].last_visit == date(2024, 11, 30)

    def test_get_practitioner_stats_with_filter(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test getting practitioner stats with filter."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data
        filter_obj = BillFilter(year=2024)

        stats = analytics_engine.get_practitioner_stats(filter_obj)

        assert len(stats) == 3
        mock_repository.get_practitioner_stats.assert_called_once_with(filter_obj)

    def test_get_practitioner_stats_with_limit(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test getting top N practitioners with limit."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data

        stats = analytics_engine.get_practitioner_stats(limit=2)

        # Should only return top 2
        assert len(stats) == 2
        assert stats[0].practitioner_name == "Dr. Schmidt"
        assert stats[1].practitioner_name == "Dr. Müller"

    def test_get_practitioner_stats_with_filter_and_limit(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test getting top N practitioners with filter and limit."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data
        filter_obj = BillFilter(year=2024, practitioner_type="Arzt")

        stats = analytics_engine.get_practitioner_stats(filter_obj, limit=1)

        assert len(stats) == 1
        assert stats[0].practitioner_name == "Dr. Schmidt"
        mock_repository.get_practitioner_stats.assert_called_once_with(filter_obj)

    def test_get_practitioner_stats_empty_results(
        self, analytics_engine, mock_repository
    ):
        """Test getting practitioner stats with no results."""
        mock_repository.get_practitioner_stats.return_value = []

        stats = analytics_engine.get_practitioner_stats()

        assert len(stats) == 0

    def test_get_practitioner_stats_returns_dataclass_instances(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test that results are PractitionerStats instances."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data

        stats = analytics_engine.get_practitioner_stats()

        for stat in stats:
            assert isinstance(stat, PractitionerStats)

    def test_get_practitioner_stats_preserves_order(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test that repository order is preserved."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data

        stats = analytics_engine.get_practitioner_stats()

        # Order should match repository (sorted by total_amount DESC)
        assert stats[0].total_amount == Decimal("500.00")
        assert stats[1].total_amount == Decimal("300.00")
        assert stats[2].total_amount == Decimal("150.00")

    def test_get_practitioner_stats_limit_larger_than_results(
        self, analytics_engine, mock_repository, sample_practitioner_data
    ):
        """Test limit larger than available results."""
        mock_repository.get_practitioner_stats.return_value = sample_practitioner_data

        stats = analytics_engine.get_practitioner_stats(limit=10)

        # Should return all available results
        assert len(stats) == 3


class TestGetCategoryStats:
    """Test get_category_stats method."""

    def test_get_category_stats_no_filter(
        self, analytics_engine, mock_repository, sample_category_data
    ):
        """Test getting category stats without filter."""
        mock_repository.get_category_stats.return_value = sample_category_data

        stats = analytics_engine.get_category_stats()

        assert len(stats) == 3
        mock_repository.get_category_stats.assert_called_once_with(None)

    def test_get_category_stats_with_filter(
        self, analytics_engine, mock_repository, sample_category_data
    ):
        """Test getting category stats with filter."""
        mock_repository.get_category_stats.return_value = sample_category_data
        filter_obj = BillFilter(year=2024)

        stats = analytics_engine.get_category_stats(filter_obj)

        assert len(stats) == 3
        mock_repository.get_category_stats.assert_called_once_with(filter_obj)

    def test_get_category_stats_calculates_percentages(
        self, analytics_engine, mock_repository, sample_category_data
    ):
        """Test that percentages are calculated correctly."""
        mock_repository.get_category_stats.return_value = sample_category_data

        stats = analytics_engine.get_category_stats()

        # Total: 500 + 450 + 50 = 1000
        # Percentages: 50%, 45%, 5%
        assert stats[0].category == "Zahnarzt"
        assert stats[0].percentage_of_total == Decimal("50.0")

        assert stats[1].category == "Arzt"
        assert stats[1].percentage_of_total == Decimal("45.0")

        assert stats[2].category == "Unknown"
        assert stats[2].percentage_of_total == Decimal("5.0")

    def test_get_category_stats_empty_results(
        self, analytics_engine, mock_repository
    ):
        """Test getting category stats with no results."""
        mock_repository.get_category_stats.return_value = []

        stats = analytics_engine.get_category_stats()

        assert len(stats) == 0

    def test_get_category_stats_single_category(
        self, analytics_engine, mock_repository
    ):
        """Test with single category (should be 100%)."""
        mock_repository.get_category_stats.return_value = [
            {
                "category": "Zahnarzt",
                "bill_count": 5,
                "total_amount": Decimal("500.00"),
                "average_amount": Decimal("100.00"),
            }
        ]

        stats = analytics_engine.get_category_stats()

        assert len(stats) == 1
        assert stats[0].percentage_of_total == Decimal("100.0")

    def test_get_category_stats_returns_dataclass_instances(
        self, analytics_engine, mock_repository, sample_category_data
    ):
        """Test that results are CategoryStats instances."""
        mock_repository.get_category_stats.return_value = sample_category_data

        stats = analytics_engine.get_category_stats()

        for stat in stats:
            assert isinstance(stat, CategoryStats)

    def test_get_category_stats_with_zero_total(
        self, analytics_engine, mock_repository
    ):
        """Test percentage calculation when total is zero."""
        mock_repository.get_category_stats.return_value = [
            {
                "category": "Test",
                "bill_count": 0,
                "total_amount": Decimal("0.00"),
                "average_amount": Decimal("0.00"),
            }
        ]

        stats = analytics_engine.get_category_stats()

        # Should handle division by zero gracefully
        assert stats[0].percentage_of_total == Decimal("0")


class TestGetMonthlyStats:
    """Test get_monthly_stats method."""

    def test_get_monthly_stats_no_filter(
        self, analytics_engine, mock_repository, sample_monthly_data
    ):
        """Test getting monthly stats without filter."""
        mock_repository.get_monthly_stats.return_value = sample_monthly_data

        stats = analytics_engine.get_monthly_stats()

        assert len(stats) == 3
        mock_repository.get_monthly_stats.assert_called_once_with(None)

    def test_get_monthly_stats_with_filter(
        self, analytics_engine, mock_repository, sample_monthly_data
    ):
        """Test getting monthly stats with filter."""
        mock_repository.get_monthly_stats.return_value = sample_monthly_data
        filter_obj = BillFilter(year=2024)

        stats = analytics_engine.get_monthly_stats(filter_obj)

        assert len(stats) == 3
        mock_repository.get_monthly_stats.assert_called_once_with(filter_obj)

    def test_get_monthly_stats_returns_correct_data(
        self, analytics_engine, mock_repository, sample_monthly_data
    ):
        """Test that monthly stats contain correct data."""
        mock_repository.get_monthly_stats.return_value = sample_monthly_data

        stats = analytics_engine.get_monthly_stats()

        # Verify first month
        assert stats[0].year == 2024
        assert stats[0].month == 1
        assert stats[0].bill_count == 3
        assert stats[0].total_amount == Decimal("250.00")
        assert stats[0].average_amount == Decimal("83.33")

        # Verify second month
        assert stats[1].year == 2024
        assert stats[1].month == 2
        assert stats[1].bill_count == 2

        # Verify third month
        assert stats[2].year == 2024
        assert stats[2].month == 3
        assert stats[2].bill_count == 5

    def test_get_monthly_stats_empty_results(self, analytics_engine, mock_repository):
        """Test getting monthly stats with no results."""
        mock_repository.get_monthly_stats.return_value = []

        stats = analytics_engine.get_monthly_stats()

        assert len(stats) == 0

    def test_get_monthly_stats_returns_dataclass_instances(
        self, analytics_engine, mock_repository, sample_monthly_data
    ):
        """Test that results are MonthlyStats instances."""
        mock_repository.get_monthly_stats.return_value = sample_monthly_data

        stats = analytics_engine.get_monthly_stats()

        for stat in stats:
            assert isinstance(stat, MonthlyStats)

    def test_get_monthly_stats_preserves_order(
        self, analytics_engine, mock_repository, sample_monthly_data
    ):
        """Test that repository order is preserved (sorted by year, month)."""
        mock_repository.get_monthly_stats.return_value = sample_monthly_data

        stats = analytics_engine.get_monthly_stats()

        # Order should be chronological
        assert stats[0].month == 1
        assert stats[1].month == 2
        assert stats[2].month == 3

    def test_get_monthly_stats_multiple_years(
        self, analytics_engine, mock_repository
    ):
        """Test monthly stats spanning multiple years."""
        data = [
            {
                "year": 2023,
                "month": 12,
                "bill_count": 2,
                "total_amount": Decimal("200.00"),
                "average_amount": Decimal("100.00"),
            },
            {
                "year": 2024,
                "month": 1,
                "bill_count": 3,
                "total_amount": Decimal("300.00"),
                "average_amount": Decimal("100.00"),
            },
        ]
        mock_repository.get_monthly_stats.return_value = data

        stats = analytics_engine.get_monthly_stats()

        assert len(stats) == 2
        assert stats[0].year == 2023
        assert stats[1].year == 2024
