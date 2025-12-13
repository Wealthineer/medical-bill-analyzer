"""Tests for database Pydantic models."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from medical_bill_analyzer.database.models import (
    Bill,
    BillCreate,
    BillFilter,
    BillUpdate,
)


class TestBillCreate:
    """Test BillCreate model."""

    def test_valid_bill_create(self):
        """Test creating valid bill."""
        bill = BillCreate(
            filename="test.pdf",
            file_hash="a" * 64,
            pdf_path="/tmp/test.pdf",
            practitioner_name="Dr. Test",
            practitioner_type="Arzt",
            bill_date=date(2024, 1, 1),
            bill_number="123",
            total_amount=Decimal("100.00"),
            currency="EUR",
        )
        assert bill.filename == "test.pdf"
        assert bill.practitioner_type == "Arzt"
        assert bill.total_amount == Decimal("100.00")

    def test_valid_practitioner_types(self):
        """Test all valid practitioner types."""
        valid_types = [
            "Arzt",
            "Zahnarzt",
            "Heilpraktiker",
            "Krankenhaus",
            "Labor",
            "Apotheke",
            "Sonstige",
        ]

        for prac_type in valid_types:
            bill = BillCreate(
                filename="test.pdf",
                file_hash="a" * 64,
                pdf_path="/tmp/test.pdf",
                practitioner_type=prac_type,
            )
            assert bill.practitioner_type == prac_type

    def test_invalid_practitioner_type(self):
        """Test invalid practitioner type raises error."""
        with pytest.raises(ValidationError) as exc:
            BillCreate(
                filename="test.pdf",
                file_hash="a" * 64,
                pdf_path="/tmp/test.pdf",
                practitioner_type="InvalidType",
            )
        assert "Invalid practitioner type" in str(exc.value)

    def test_file_hash_length_validation(self):
        """Test file hash must be exactly 64 characters (SHA256)."""
        # Too short
        with pytest.raises(ValidationError):
            BillCreate(
                filename="test.pdf",
                file_hash="short",
                pdf_path="/tmp/test.pdf",
            )

        # Too long
        with pytest.raises(ValidationError):
            BillCreate(
                filename="test.pdf",
                file_hash="a" * 65,
                pdf_path="/tmp/test.pdf",
            )

    def test_negative_amount_validation(self):
        """Test negative amounts are rejected."""
        with pytest.raises(ValidationError):
            BillCreate(
                filename="test.pdf",
                file_hash="a" * 64,
                pdf_path="/tmp/test.pdf",
                total_amount=Decimal("-100.00"),
            )

    def test_default_values(self):
        """Test default values are set correctly."""
        bill = BillCreate(
            filename="test.pdf",
            file_hash="a" * 64,
            pdf_path="/tmp/test.pdf",
        )
        assert bill.currency == "EUR"
        assert bill.extraction_status == "success"

    def test_optional_fields(self):
        """Test optional fields can be None."""
        bill = BillCreate(
            filename="test.pdf",
            file_hash="a" * 64,
            pdf_path="/tmp/test.pdf",
        )
        assert bill.practitioner_name is None
        assert bill.bill_date is None
        assert bill.total_amount is None


class TestBillUpdate:
    """Test BillUpdate model."""

    def test_all_fields_optional(self):
        """Test all fields are optional in update."""
        update = BillUpdate()
        assert update.practitioner_name is None
        assert update.total_amount is None

    def test_partial_update(self):
        """Test updating only some fields."""
        update = BillUpdate(
            practitioner_name="Dr. Updated",
            total_amount=Decimal("200.00"),
        )
        assert update.practitioner_name == "Dr. Updated"
        assert update.total_amount == Decimal("200.00")
        assert update.bill_date is None

    def test_practitioner_type_validation(self):
        """Test practitioner type is validated in updates."""
        with pytest.raises(ValidationError):
            BillUpdate(practitioner_type="InvalidType")

    def test_valid_status_values(self):
        """Test valid extraction status values."""
        valid_statuses = ["success", "failed", "needs_review"]

        for status in valid_statuses:
            update = BillUpdate(extraction_status=status)
            assert update.extraction_status == status


class TestBillFilter:
    """Test BillFilter model."""

    def test_valid_filter(self):
        """Test creating valid filter."""
        filter_obj = BillFilter(
            year=2024,
            practitioner_type="Arzt",
            min_amount=Decimal("50.00"),
            max_amount=Decimal("500.00"),
        )
        assert filter_obj.year == 2024
        assert filter_obj.min_amount == Decimal("50.00")

    def test_date_range_validation(self):
        """Test end_date must be after start_date."""
        with pytest.raises(ValidationError) as exc:
            BillFilter(
                start_date=date(2024, 12, 31),
                end_date=date(2024, 1, 1),
            )
        assert "end_date must be after start_date" in str(exc.value)

    def test_valid_date_range(self):
        """Test valid date range."""
        filter_obj = BillFilter(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert filter_obj.start_date < filter_obj.end_date

    def test_year_validation(self):
        """Test year must be reasonable."""
        # Too early
        with pytest.raises(ValidationError):
            BillFilter(year=1800)

        # Too late
        with pytest.raises(ValidationError):
            BillFilter(year=2200)

        # Valid
        filter_obj = BillFilter(year=2024)
        assert filter_obj.year == 2024

    def test_negative_amounts_rejected(self):
        """Test negative amounts are rejected in filters."""
        with pytest.raises(ValidationError):
            BillFilter(min_amount=Decimal("-10.00"))

        with pytest.raises(ValidationError):
            BillFilter(max_amount=Decimal("-50.00"))

    def test_all_fields_optional(self):
        """Test filter can be empty."""
        filter_obj = BillFilter()
        assert filter_obj.year is None
        assert filter_obj.start_date is None


class TestBill:
    """Test Bill model (with database fields)."""

    def test_from_dict(self):
        """Test creating Bill from dictionary (database row)."""
        from datetime import datetime

        bill_dict = {
            "id": 1,
            "filename": "test.pdf",
            "file_hash": "a" * 64,
            "pdf_path": "/tmp/test.pdf",
            "practitioner_name": "Dr. Test",
            "practitioner_type": "Arzt",
            "bill_date": date(2024, 1, 1),
            "bill_number": "123",
            "total_amount": Decimal("100.00"),
            "currency": "EUR",
            "processed_at": datetime.now(),
            "extraction_status": "success",
            "raw_extraction_json": None,
            "notes": None,
        }

        bill = Bill(**bill_dict)
        assert bill.id == 1
        assert bill.filename == "test.pdf"
        assert bill.practitioner_name == "Dr. Test"

    def test_bill_has_required_fields(self):
        """Test Bill requires id and processed_at."""
        from datetime import datetime

        # Missing id
        with pytest.raises(ValidationError):
            Bill(
                filename="test.pdf",
                file_hash="a" * 64,
                pdf_path="/tmp/test.pdf",
                processed_at=datetime.now(),
            )

        # Missing processed_at
        with pytest.raises(ValidationError):
            Bill(
                id=1,
                filename="test.pdf",
                file_hash="a" * 64,
                pdf_path="/tmp/test.pdf",
            )
