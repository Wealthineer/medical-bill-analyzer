"""Tests for BillRepository."""

from datetime import date
from decimal import Decimal

import pytest

from medical_bill_analyzer.core.exceptions import DatabaseError, DuplicateBillError
from medical_bill_analyzer.database.models import BillFilter, BillUpdate


class TestBillRepositoryCreate:
    """Test bill creation."""

    def test_create_bill(self, bill_repository, sample_bill_create):
        """Test creating a bill."""
        bill = bill_repository.create(sample_bill_create)

        assert bill.id is not None
        assert bill.filename == sample_bill_create.filename
        assert bill.practitioner_name == sample_bill_create.practitioner_name
        assert bill.total_amount == sample_bill_create.total_amount
        assert bill.processed_at is not None

    def test_create_bill_with_decimal_amount(self, bill_repository, sample_bill_create):
        """Test Decimal amounts are preserved."""
        bill = bill_repository.create(sample_bill_create)

        assert isinstance(bill.total_amount, Decimal)
        assert bill.total_amount == Decimal("120.50")

    def test_create_duplicate_hash_raises_error(
        self, bill_repository, sample_bill_create
    ):
        """Test creating bill with duplicate hash raises error."""
        bill_repository.create(sample_bill_create)

        # Try to create another with same hash
        with pytest.raises(DuplicateBillError) as exc:
            bill_repository.create(sample_bill_create)

        assert "file hash" in str(exc.value).lower()

    def test_create_duplicate_filename_raises_error(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test creating bill with duplicate filename raises error."""
        bill_repository.create(sample_bill_create)

        # Create another with same filename but different hash
        sample_bill_create_2.filename = sample_bill_create.filename

        with pytest.raises(DuplicateBillError) as exc:
            bill_repository.create(sample_bill_create_2)

        assert "filename" in str(exc.value).lower()


class TestBillRepositoryRead:
    """Test bill retrieval."""

    def test_get_by_id(self, bill_repository, created_bill):
        """Test retrieving bill by ID."""
        bill = bill_repository.get_by_id(created_bill.id)

        assert bill is not None
        assert bill.id == created_bill.id
        assert bill.filename == created_bill.filename

    def test_get_by_id_nonexistent(self, bill_repository):
        """Test getting non-existent bill returns None."""
        bill = bill_repository.get_by_id(99999)

        assert bill is None

    def test_get_by_filename(self, bill_repository, created_bill):
        """Test retrieving bill by filename."""
        bill = bill_repository.get_by_filename(created_bill.filename)

        assert bill is not None
        assert bill.id == created_bill.id

    def test_get_by_filename_nonexistent(self, bill_repository):
        """Test getting non-existent filename returns None."""
        bill = bill_repository.get_by_filename("nonexistent.pdf")

        assert bill is None

    def test_get_all(self, bill_repository, sample_bill_create, sample_bill_create_2):
        """Test getting all bills."""
        bill_repository.create(sample_bill_create)
        bill_repository.create(sample_bill_create_2)

        bills = bill_repository.get_all()

        assert len(bills) == 2

    def test_get_all_with_limit(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test getting bills with limit."""
        bill_repository.create(sample_bill_create)
        bill_repository.create(sample_bill_create_2)

        bills = bill_repository.get_all(limit=1)

        assert len(bills) == 1

    def test_get_all_ordered_by_date_desc(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test bills are ordered by date descending."""
        bill1 = bill_repository.create(sample_bill_create)  # Dec 1
        bill2 = bill_repository.create(sample_bill_create_2)  # Nov 15

        bills = bill_repository.get_all()

        # Most recent first
        assert bills[0].id == bill1.id
        assert bills[1].id == bill2.id


class TestBillRepositoryUpdate:
    """Test bill updates."""

    def test_update_bill(self, bill_repository, created_bill):
        """Test updating bill fields."""
        updates = BillUpdate(
            practitioner_name="Dr. Updated",
            total_amount=Decimal("200.00"),
            notes="Updated note",
        )

        updated = bill_repository.update(created_bill.id, updates)

        assert updated.practitioner_name == "Dr. Updated"
        assert updated.total_amount == Decimal("200.00")
        assert updated.notes == "Updated note"
        # Other fields unchanged
        assert updated.filename == created_bill.filename

    def test_update_nonexistent_raises_error(self, bill_repository):
        """Test updating non-existent bill raises error."""
        updates = BillUpdate(practitioner_name="Test")

        with pytest.raises(DatabaseError):
            bill_repository.update(99999, updates)

    def test_update_empty_does_nothing(self, bill_repository, created_bill):
        """Test update with no fields returns unchanged bill."""
        updates = BillUpdate()

        updated = bill_repository.update(created_bill.id, updates)

        assert updated.practitioner_name == created_bill.practitioner_name
        assert updated.total_amount == created_bill.total_amount


class TestBillRepositoryDelete:
    """Test bill deletion."""

    def test_delete_bill(self, bill_repository, created_bill):
        """Test deleting a bill."""
        result = bill_repository.delete(created_bill.id)

        assert result is True

        # Verify deleted
        bill = bill_repository.get_by_id(created_bill.id)
        assert bill is None

    def test_delete_nonexistent(self, bill_repository):
        """Test deleting non-existent bill returns False."""
        result = bill_repository.delete(99999)

        assert result is False


class TestBillRepositoryDuplicateDetection:
    """Test duplicate detection."""

    def test_check_duplicate_hash(self, bill_repository, created_bill):
        """Test checking for duplicate hash."""
        is_duplicate = bill_repository.check_duplicate_hash(created_bill.file_hash)

        assert is_duplicate is True

    def test_check_duplicate_hash_nonexistent(self, bill_repository):
        """Test checking non-existent hash."""
        is_duplicate = bill_repository.check_duplicate_hash("x" * 64)

        assert is_duplicate is False


class TestBillRepositoryDateFiltering:
    """Test date-based filtering."""

    def test_get_by_date_range(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test getting bills by date range."""
        bill_repository.create(sample_bill_create)  # Dec 1, 2024
        bill_repository.create(sample_bill_create_2)  # Nov 15, 2024

        bills = bill_repository.get_by_date_range(
            date(2024, 11, 1), date(2024, 11, 30)
        )

        assert len(bills) == 1
        assert bills[0].bill_date == date(2024, 11, 15)

    def test_get_by_date_range_inclusive(self, bill_repository, sample_bill_create):
        """Test date range is inclusive."""
        bill_repository.create(sample_bill_create)  # Dec 1

        # Start date matches bill date
        bills = bill_repository.get_by_date_range(
            date(2024, 12, 1), date(2024, 12, 31)
        )
        assert len(bills) == 1

        # End date matches bill date
        bills = bill_repository.get_by_date_range(
            date(2024, 11, 1), date(2024, 12, 1)
        )
        assert len(bills) == 1

    def test_get_by_year(self, bill_repository, sample_bill_create):
        """Test getting bills by year."""
        sample_bill_create.bill_date = date(2024, 6, 15)
        bill_repository.create(sample_bill_create)

        bills = bill_repository.get_by_year(2024)

        assert len(bills) == 1

    def test_get_by_year_empty(self, bill_repository):
        """Test getting bills for year with no bills."""
        bills = bill_repository.get_by_year(2020)

        assert len(bills) == 0


class TestBillRepositoryStatusFiltering:
    """Test status-based filtering."""

    def test_get_by_status(self, bill_repository, sample_bill_create):
        """Test getting bills by extraction status."""
        sample_bill_create.extraction_status = "needs_review"
        bill_repository.create(sample_bill_create)

        bills = bill_repository.get_by_status("needs_review")

        assert len(bills) == 1
        assert bills[0].extraction_status == "needs_review"

    def test_get_by_status_empty(self, bill_repository):
        """Test getting bills with status that doesn't exist."""
        bills = bill_repository.get_by_status("failed")

        assert len(bills) == 0


class TestBillRepositoryFilter:
    """Test multi-criteria filtering."""

    def test_filter_by_year(self, bill_repository, sample_bill_create):
        """Test filtering by year."""
        bill_repository.create(sample_bill_create)

        filter_obj = BillFilter(year=2024)
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 1

    def test_filter_by_practitioner_name(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test filtering by practitioner name."""
        bill_repository.create(sample_bill_create)  # Dr. Schmidt
        bill_repository.create(sample_bill_create_2)  # Dr. Müller

        filter_obj = BillFilter(practitioner_name="Schmidt")
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 1
        assert "Schmidt" in bills[0].practitioner_name

    def test_filter_by_practitioner_type(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test filtering by practitioner type."""
        bill_repository.create(sample_bill_create)  # Arzt
        bill_repository.create(sample_bill_create_2)  # Zahnarzt

        filter_obj = BillFilter(practitioner_type="Zahnarzt")
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 1
        assert bills[0].practitioner_type == "Zahnarzt"

    def test_filter_by_amount_range(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test filtering by amount range."""
        bill_repository.create(sample_bill_create)  # 120.50
        bill_repository.create(sample_bill_create_2)  # 250.00

        filter_obj = BillFilter(
            min_amount=Decimal("200.00"), max_amount=Decimal("300.00")
        )
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 1
        assert bills[0].total_amount == Decimal("250.00")

    def test_filter_by_date_range(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test filtering by date range."""
        bill_repository.create(sample_bill_create)  # Dec 1
        bill_repository.create(sample_bill_create_2)  # Nov 15

        filter_obj = BillFilter(
            start_date=date(2024, 11, 1), end_date=date(2024, 11, 30)
        )
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 1

    def test_filter_multiple_criteria(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test filtering with multiple criteria."""
        bill_repository.create(sample_bill_create)
        bill_repository.create(sample_bill_create_2)

        filter_obj = BillFilter(
            year=2024, practitioner_type="Arzt", min_amount=Decimal("100.00")
        )
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 1
        assert bills[0].practitioner_type == "Arzt"

    def test_filter_empty_result(self, bill_repository):
        """Test filter with no matching results."""
        filter_obj = BillFilter(year=2020)
        bills = bill_repository.filter(filter_obj)

        assert len(bills) == 0


class TestBillRepositoryAggregates:
    """Test aggregate functions."""

    def test_get_total_amount_all(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test calculating total amount of all bills."""
        bill_repository.create(sample_bill_create)  # 120.50
        bill_repository.create(sample_bill_create_2)  # 250.00

        total = bill_repository.get_total_amount()

        assert total == Decimal("370.50")

    def test_get_total_amount_by_year(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test calculating total amount by year."""
        bill_repository.create(sample_bill_create)  # 2024
        sample_bill_create_2.bill_date = date(2023, 1, 1)
        bill_repository.create(sample_bill_create_2)  # 2023

        total = bill_repository.get_total_amount(year=2024)

        assert total == Decimal("120.50")

    def test_get_total_amount_by_date_range(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test calculating total by date range."""
        bill_repository.create(sample_bill_create)  # Dec 1
        bill_repository.create(sample_bill_create_2)  # Nov 15

        total = bill_repository.get_total_amount(
            start_date=date(2024, 11, 1), end_date=date(2024, 11, 30)
        )

        assert total == Decimal("250.00")

    def test_get_total_amount_empty(self, bill_repository):
        """Test total amount with no bills."""
        total = bill_repository.get_total_amount()

        assert total == Decimal("0")

    def test_get_total_amount_returns_decimal(
        self, bill_repository, sample_bill_create
    ):
        """Test total amount returns Decimal type."""
        bill_repository.create(sample_bill_create)

        total = bill_repository.get_total_amount()

        assert isinstance(total, Decimal)

    def test_count_all(self, bill_repository, sample_bill_create, sample_bill_create_2):
        """Test counting all bills."""
        bill_repository.create(sample_bill_create)
        bill_repository.create(sample_bill_create_2)

        count = bill_repository.count()

        assert count == 2

    def test_count_with_filter(
        self, bill_repository, sample_bill_create, sample_bill_create_2
    ):
        """Test counting with filter."""
        bill_repository.create(sample_bill_create)  # Arzt
        bill_repository.create(sample_bill_create_2)  # Zahnarzt

        filter_obj = BillFilter(practitioner_type="Arzt")
        count = bill_repository.count(filter_obj)

        assert count == 1

    def test_count_empty(self, bill_repository):
        """Test count with no bills."""
        count = bill_repository.count()

        assert count == 0
