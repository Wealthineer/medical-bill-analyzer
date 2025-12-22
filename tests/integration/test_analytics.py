"""Integration tests for analytics with real database."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from medical_bill_analyzer.analytics.engine import AnalyticsEngine
from medical_bill_analyzer.database.connection import DatabaseConnection
from medical_bill_analyzer.database.migrations.migration_manager import (
    MigrationManager,
)
from medical_bill_analyzer.database.models import BillCreate, BillFilter
from medical_bill_analyzer.database.repositories.bill_repository import BillRepository


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample bills."""
    db_path = tmp_path / "test_analytics.db"

    # Run migrations
    manager = MigrationManager(db_path)
    manager.migrate()

    # Create repository
    repository = BillRepository(db_path)

    # Add sample bills spanning multiple practitioners, categories, and months
    bills = [
        # Dr. Schmidt - Zahnarzt (5 bills, Jan-Nov 2024)
        BillCreate(
            filename="schmidt_1.pdf",
            file_hash="a" * 64,  # SHA256 hash (64 hex chars)
            pdf_path="/tmp/schmidt_1.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_date=date(2024, 1, 15),
            bill_number="Z-001",
            total_amount=Decimal("100.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="schmidt_2.pdf",
            file_hash="b" * 64,
            pdf_path="/tmp/schmidt_2.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_date=date(2024, 3, 20),
            bill_number="Z-002",
            total_amount=Decimal("120.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="schmidt_3.pdf",
            file_hash="c" * 64,
            pdf_path="/tmp/schmidt_3.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_date=date(2024, 6, 10),
            bill_number="Z-003",
            total_amount=Decimal("80.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="schmidt_4.pdf",
            file_hash="d" * 64,
            pdf_path="/tmp/schmidt_4.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_date=date(2024, 9, 5),
            bill_number="Z-004",
            total_amount=Decimal("150.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="schmidt_5.pdf",
            file_hash="e" * 64,
            pdf_path="/tmp/schmidt_5.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_date=date(2024, 11, 30),
            bill_number="Z-005",
            total_amount=Decimal("50.00"),
            currency="EUR",
            extraction_status="success",
        ),
        # Dr. Müller - Arzt (3 bills, Feb-Sep 2024)
        BillCreate(
            filename="mueller_1.pdf",
            file_hash="f" * 64,
            pdf_path="/tmp/mueller_1.pdf",
            practitioner_name="Dr. Müller",
            practitioner_type="Arzt",
            bill_date=date(2024, 2, 10),
            bill_number="A-001",
            total_amount=Decimal("90.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="mueller_2.pdf",
            file_hash="1" * 64,
            pdf_path="/tmp/mueller_2.pdf",
            practitioner_name="Dr. Müller",
            practitioner_type="Arzt",
            bill_date=date(2024, 5, 15),
            bill_number="A-002",
            total_amount=Decimal("110.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="mueller_3.pdf",
            file_hash="2" * 64,
            pdf_path="/tmp/mueller_3.pdf",
            practitioner_name="Dr. Müller",
            practitioner_type="Arzt",
            bill_date=date(2024, 9, 20),
            bill_number="A-003",
            total_amount=Decimal("100.00"),
            currency="EUR",
            extraction_status="success",
        ),
        # Dr. Weber - Arzt (2 bills, Jun-Aug 2024)
        BillCreate(
            filename="weber_1.pdf",
            file_hash="3" * 64,
            pdf_path="/tmp/weber_1.pdf",
            practitioner_name="Dr. Weber",
            practitioner_type="Arzt",
            bill_date=date(2024, 6, 1),
            bill_number="A-004",
            total_amount=Decimal("75.00"),
            currency="EUR",
            extraction_status="success",
        ),
        BillCreate(
            filename="weber_2.pdf",
            file_hash="4" * 64,
            pdf_path="/tmp/weber_2.pdf",
            practitioner_name="Dr. Weber",
            practitioner_type="Arzt",
            bill_date=date(2024, 8, 15),
            bill_number="A-005",
            total_amount=Decimal("75.00"),
            currency="EUR",
            extraction_status="success",
        ),
        # 2023 bill for time-series testing
        BillCreate(
            filename="old_bill.pdf",
            file_hash="5" * 64,
            pdf_path="/tmp/old_bill.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Zahnarzt",
            bill_date=date(2023, 12, 15),
            bill_number="Z-000",
            total_amount=Decimal("60.00"),
            currency="EUR",
            extraction_status="success",
        ),
    ]

    for bill in bills:
        repository.create(bill)

    return db_path, repository


class TestPractitionerStatsIntegration:
    """Integration tests for practitioner statistics."""

    def test_get_practitioner_stats_all(self, test_db):
        """Test getting all practitioner stats."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        stats = engine.get_practitioner_stats()

        # Should have 3 practitioners (Schmidt, Müller, Weber)
        assert len(stats) == 3

        # Check sorted by total_amount descending
        assert stats[0].practitioner_name == "Dr. Schmidt"
        assert stats[0].total_amount == Decimal("560.00")  # 6 bills total (including 2023)
        assert stats[0].bill_count == 6

        assert stats[1].practitioner_name == "Dr. Müller"
        assert stats[1].total_amount == Decimal("300.00")
        assert stats[1].bill_count == 3

        assert stats[2].practitioner_name == "Dr. Weber"
        assert stats[2].total_amount == Decimal("150.00")
        assert stats[2].bill_count == 2

    def test_get_practitioner_stats_with_year_filter(self, test_db):
        """Test practitioner stats filtered by year."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(year=2024)
        stats = engine.get_practitioner_stats(filter_obj)

        # Should exclude 2023 bill
        assert len(stats) == 3
        assert stats[0].practitioner_name == "Dr. Schmidt"
        assert stats[0].total_amount == Decimal("500.00")  # Only 2024 bills
        assert stats[0].bill_count == 5

    def test_get_practitioner_stats_with_limit(self, test_db):
        """Test practitioner stats with limit."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        stats = engine.get_practitioner_stats(limit=2)

        # Should only return top 2
        assert len(stats) == 2
        assert stats[0].practitioner_name == "Dr. Schmidt"
        assert stats[1].practitioner_name == "Dr. Müller"

    def test_get_practitioner_stats_with_type_filter(self, test_db):
        """Test practitioner stats filtered by type."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(practitioner_type="Arzt")
        stats = engine.get_practitioner_stats(filter_obj)

        # Should only include Arzt practitioners
        assert len(stats) == 2
        assert all(s.practitioner_type == "Arzt" for s in stats)

        assert stats[0].practitioner_name == "Dr. Müller"
        assert stats[0].total_amount == Decimal("300.00")

        assert stats[1].practitioner_name == "Dr. Weber"
        assert stats[1].total_amount == Decimal("150.00")

    def test_practitioner_stats_date_ranges(self, test_db):
        """Test that first_visit and last_visit are correct."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(year=2024)
        stats = engine.get_practitioner_stats(filter_obj)

        schmidt = next(s for s in stats if s.practitioner_name == "Dr. Schmidt")
        assert schmidt.first_visit == date(2024, 1, 15)
        assert schmidt.last_visit == date(2024, 11, 30)
        assert schmidt.visit_span_days == 320  # Days between Jan 15 and Nov 30


class TestCategoryStatsIntegration:
    """Integration tests for category statistics."""

    def test_get_category_stats_all(self, test_db):
        """Test getting all category stats."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        stats = engine.get_category_stats()

        # Should have 2 categories (Zahnarzt, Arzt)
        assert len(stats) == 2

        # Check sorted by total_amount descending
        assert stats[0].category == "Zahnarzt"
        assert stats[0].total_amount == Decimal("560.00")
        assert stats[0].bill_count == 6

        assert stats[1].category == "Arzt"
        assert stats[1].total_amount == Decimal("450.00")
        assert stats[1].bill_count == 5

    def test_category_stats_percentages(self, test_db):
        """Test that percentages are calculated correctly."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        stats = engine.get_category_stats()

        # Total: 560 + 450 = 1010
        # Zahnarzt: 560/1010 = 55.45%
        # Arzt: 450/1010 = 44.55%
        total = Decimal("1010.00")

        zahnarzt = next(s for s in stats if s.category == "Zahnarzt")
        assert abs(zahnarzt.percentage_of_total - (Decimal("560") / total * 100)) < Decimal("0.01")
        assert zahnarzt.is_major_category  # >20%

        arzt = next(s for s in stats if s.category == "Arzt")
        assert abs(arzt.percentage_of_total - (Decimal("450") / total * 100)) < Decimal("0.01")
        assert arzt.is_major_category  # >20%

    def test_get_category_stats_with_year_filter(self, test_db):
        """Test category stats filtered by year."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(year=2024)
        stats = engine.get_category_stats(filter_obj)

        # Should exclude 2023 bill
        zahnarzt = next(s for s in stats if s.category == "Zahnarzt")
        assert zahnarzt.total_amount == Decimal("500.00")  # Only 2024
        assert zahnarzt.bill_count == 5

        arzt = next(s for s in stats if s.category == "Arzt")
        assert arzt.total_amount == Decimal("450.00")
        assert arzt.bill_count == 5


class TestMonthlyStatsIntegration:
    """Integration tests for monthly statistics."""

    def test_get_monthly_stats_all(self, test_db):
        """Test getting all monthly stats."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        stats = engine.get_monthly_stats()

        # Should have months from 2023-12 through 2024-11 with bills
        # Expected months: 2023-12, 2024-01, 02, 03, 05, 06, 08, 09, 11
        assert len(stats) == 9

        # Verify chronological order
        assert stats[0].year == 2023
        assert stats[0].month == 12
        assert stats[1].year == 2024
        assert stats[1].month == 1

    def test_get_monthly_stats_with_year_filter(self, test_db):
        """Test monthly stats filtered by year."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(year=2024)
        stats = engine.get_monthly_stats(filter_obj)

        # Should only include 2024 months
        assert all(s.year == 2024 for s in stats)
        assert len(stats) == 8  # Jan, Feb, Mar, May, Jun, Aug, Sep, Nov

        # Check specific months
        jan = next(s for s in stats if s.month == 1)
        assert jan.bill_count == 1
        assert jan.total_amount == Decimal("100.00")

        jun = next(s for s in stats if s.month == 6)
        assert jun.bill_count == 2  # Schmidt + Weber
        assert jun.total_amount == Decimal("155.00")

    def test_get_monthly_stats_with_type_filter(self, test_db):
        """Test monthly stats filtered by practitioner type."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(practitioner_type="Zahnarzt")
        stats = engine.get_monthly_stats(filter_obj)

        # Should only include Zahnarzt bills
        # Months: 2023-12, 2024-01, 03, 06, 09, 11
        assert len(stats) == 6

        # All should be from Dr. Schmidt (the only Zahnarzt)
        for stat in stats:
            assert stat.bill_count >= 1

    def test_monthly_stats_properties(self, test_db):
        """Test that monthly stats properties work correctly."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        filter_obj = BillFilter(year=2024)
        stats = engine.get_monthly_stats(filter_obj)

        # Check January
        jan = next(s for s in stats if s.month == 1)
        assert jan.period == "2024-01"
        assert jan.month_name == "Jan"

        # Check June
        jun = next(s for s in stats if s.month == 6)
        assert jun.period == "2024-06"
        assert jun.month_name == "Jun"


class TestAnalyticsEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_database(self, tmp_path):
        """Test analytics with empty database."""
        db_path = tmp_path / "empty.db"
        manager = MigrationManager(db_path)
        manager.migrate()

        repository = BillRepository(db_path)
        engine = AnalyticsEngine(repository)

        # All should return empty lists
        assert engine.get_practitioner_stats() == []
        assert engine.get_category_stats() == []
        assert engine.get_monthly_stats() == []

    def test_filter_with_no_results(self, test_db):
        """Test filtering that yields no results."""
        db_path, repository = test_db
        engine = AnalyticsEngine(repository)

        # Filter for non-existent year
        filter_obj = BillFilter(year=2025)
        assert engine.get_practitioner_stats(filter_obj) == []
        assert engine.get_category_stats(filter_obj) == []
        assert engine.get_monthly_stats(filter_obj) == []

        # Filter for non-existent type (only works for practitioner and monthly stats)
        # Category stats groups BY type, so filtering by type doesn't make sense
        filter_obj = BillFilter(practitioner_type="Heilpraktiker")
        assert engine.get_practitioner_stats(filter_obj) == []
        assert engine.get_monthly_stats(filter_obj) == []
