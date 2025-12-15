"""Tests for extraction result models."""

from datetime import date
from pathlib import Path

import pytest

from medical_bill_analyzer.extraction.result import ExtractionResult, ExtractionStatus


class TestExtractionStatus:
    """Test ExtractionStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        assert ExtractionStatus.SUCCESS == "success"
        assert ExtractionStatus.PDF_INVALID == "pdf_invalid"
        assert ExtractionStatus.PDF_NOT_PROCESSABLE == "pdf_not_processable"
        assert ExtractionStatus.EXTRACTION_FAILED == "extraction_failed"
        assert ExtractionStatus.VALIDATION_FAILED == "validation_failed"


class TestExtractionResult:
    """Test ExtractionResult dataclass."""

    def test_create_success_result(self):
        """Test creating successful extraction result."""
        extracted_data = {
            "practitioner_name": "Dr. med. Anna Müller",
            "practitioner_type": "Arzt",
            "bill_date": date(2024, 3, 15),
            "bill_number": "2024-001234",
            "total_amount": 29.49,
            "currency": "EUR",
        }

        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
            extracted_data=extracted_data,
        )

        assert result.status == ExtractionStatus.SUCCESS
        assert result.pdf_path == Path("test.pdf")
        assert result.pdf_hash == "abc123"
        assert result.extracted_data == extracted_data
        assert result.errors == []
        assert result.warnings == []

    def test_convenience_properties_populated(self):
        """Test that convenience properties are populated from extracted_data."""
        extracted_data = {
            "practitioner_name": "Dr. Smith",
            "practitioner_type": "Arzt",
            "bill_date": date(2024, 1, 1),
            "bill_number": "B-123",
            "total_amount": 50.0,
            "currency": "EUR",
        }

        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
            extracted_data=extracted_data,
        )

        assert result.practitioner_name == "Dr. Smith"
        assert result.practitioner_type == "Arzt"
        assert result.bill_date == date(2024, 1, 1)
        assert result.bill_number == "B-123"
        assert result.total_amount == 50.0
        assert result.currency == "EUR"

    def test_convenience_properties_none_when_no_data(self):
        """Test convenience properties are None when extracted_data is None."""
        result = ExtractionResult(
            status=ExtractionStatus.PDF_INVALID,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
            extracted_data=None,
        )

        assert result.practitioner_name is None
        assert result.practitioner_type is None
        assert result.bill_date is None
        assert result.bill_number is None
        assert result.total_amount is None
        assert result.currency is None

    def test_is_success_property(self):
        """Test is_success property."""
        success_result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )
        assert success_result.is_success is True

        failed_result = ExtractionResult(
            status=ExtractionStatus.EXTRACTION_FAILED,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )
        assert failed_result.is_success is False

    def test_is_processable_property(self):
        """Test is_processable property."""
        # Success is processable
        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )
        assert result.is_processable is True

        # Extraction failed is processable (PDF was valid)
        result = ExtractionResult(
            status=ExtractionStatus.EXTRACTION_FAILED,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )
        assert result.is_processable is True

        # Invalid PDF is not processable
        result = ExtractionResult(
            status=ExtractionStatus.PDF_INVALID,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )
        assert result.is_processable is False

        # Scanned PDF is not processable
        result = ExtractionResult(
            status=ExtractionStatus.PDF_NOT_PROCESSABLE,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )
        assert result.is_processable is False

    def test_result_with_errors_and_warnings(self):
        """Test result with errors and warnings."""
        result = ExtractionResult(
            status=ExtractionStatus.PDF_INVALID,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
            errors=["Corrupted file", "Cannot read"],
            warnings=["Large file size"],
        )

        assert result.errors == ["Corrupted file", "Cannot read"]
        assert result.warnings == ["Large file size"]

    def test_to_dict_method(self):
        """Test to_dict serialization."""
        extracted_data = {
            "practitioner_name": "Dr. Müller",
            "practitioner_type": "Arzt",
            "bill_date": date(2024, 3, 15),
            "bill_number": "B-123",
            "total_amount": 29.49,
            "currency": "EUR",
        }

        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
            extracted_data=extracted_data,
            warnings=["Test warning"],
        )

        result_dict = result.to_dict()

        assert result_dict["status"] == "success"
        assert result_dict["pdf_path"] == "test.pdf"
        assert result_dict["pdf_hash"] == "abc123"
        assert result_dict["extracted_data"] == extracted_data
        assert result_dict["errors"] == []
        assert result_dict["warnings"] == ["Test warning"]
        assert result_dict["practitioner_name"] == "Dr. Müller"
        assert result_dict["practitioner_type"] == "Arzt"
        assert result_dict["bill_date"] == "2024-03-15"
        assert result_dict["bill_number"] == "B-123"
        assert result_dict["total_amount"] == 29.49
        assert result_dict["currency"] == "EUR"

    def test_to_dict_with_none_date(self):
        """Test to_dict with None bill_date."""
        result = ExtractionResult(
            status=ExtractionStatus.EXTRACTION_FAILED,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
        )

        result_dict = result.to_dict()
        assert result_dict["bill_date"] is None

    def test_currency_defaults_to_eur_when_missing(self):
        """Test currency defaults to EUR if not in extracted_data."""
        extracted_data = {
            "practitioner_name": "Dr. Smith",
            "total_amount": 50.0,
            # currency not specified
        }

        result = ExtractionResult(
            status=ExtractionStatus.SUCCESS,
            pdf_path=Path("test.pdf"),
            pdf_hash="abc123",
            extracted_data=extracted_data,
        )

        # Should default to EUR (from __post_init__)
        assert result.currency == "EUR"
