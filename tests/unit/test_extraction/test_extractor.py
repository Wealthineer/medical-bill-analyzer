"""Tests for bill extractor."""

from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from medical_bill_analyzer.core.exceptions import (
    LLMExtractionError,
    PDFProcessingError,
    ValidationError,
)
from medical_bill_analyzer.extraction.extractor import BillExtractor
from medical_bill_analyzer.extraction.result import ExtractionStatus
from medical_bill_analyzer.pdf.validator import ValidationResult


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    provider = Mock()
    provider.__class__.__name__ = "MockProvider"
    return provider


@pytest.fixture
def extractor(mock_llm_provider):
    """Create BillExtractor with mock provider."""
    return BillExtractor(mock_llm_provider)


class TestBillExtractorInit:
    """Test BillExtractor initialization."""

    def test_initialization(self, mock_llm_provider):
        """Test extractor initializes with LLM provider."""
        extractor = BillExtractor(mock_llm_provider)
        assert extractor.llm_provider == mock_llm_provider


class TestExtractFromPDF:
    """Test extract_from_pdf method."""

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_successful_extraction(
        self, mock_extract_text, mock_validate, mock_hash, extractor, mock_llm_provider
    ):
        """Test successful end-to-end extraction."""
        # Setup mocks
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            is_scanned=False,
            page_count=1,
            has_text=True,
        )
        mock_extract_text.return_value = "Rechnung Dr. med. Müller 29.49 EUR"
        mock_llm_provider.extract.return_value = {
            "practitioner_name": "Dr. med. Müller",
            "practitioner_type": "Arzt",
            "bill_date": date(2024, 3, 15),
            "bill_number": "2024-001234",
            "total_amount": 29.49,
            "currency": "EUR",
        }

        # Extract
        result = extractor.extract_from_pdf(pdf_path)

        # Verify
        assert result.status == ExtractionStatus.SUCCESS
        assert result.is_success is True
        assert result.pdf_path == pdf_path
        assert result.pdf_hash == "abc123"
        assert result.practitioner_name == "Dr. med. Müller"
        assert result.practitioner_type == "Arzt"
        assert result.total_amount == 29.49
        assert result.errors == []

        # Verify method calls
        mock_hash.assert_called_once_with(pdf_path)
        mock_validate.assert_called_once_with(pdf_path)
        mock_extract_text.assert_called_once_with(pdf_path)
        mock_llm_provider.extract.assert_called_once_with(
            "Rechnung Dr. med. Müller 29.49 EUR", "basic"
        )

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    def test_pdf_hash_calculation_fails(self, mock_hash, extractor):
        """Test extraction when PDF hash calculation fails."""
        pdf_path = Path("nonexistent.pdf")
        mock_hash.side_effect = FileNotFoundError("File not found")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.PDF_INVALID
        assert result.is_success is False
        assert "Failed to access PDF file" in result.errors[0]
        assert result.pdf_hash == ""

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    def test_pdf_validation_fails(self, mock_validate, mock_hash, extractor):
        """Test extraction when PDF validation fails."""
        pdf_path = Path("corrupted.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.side_effect = Exception("Corrupted PDF")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.PDF_INVALID
        assert result.is_success is False
        assert "PDF validation failed" in result.errors[0]
        assert result.pdf_hash == "abc123"

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    def test_pdf_not_processable_scanned(self, mock_validate, mock_hash, extractor):
        """Test extraction with scanned PDF."""
        pdf_path = Path("scanned.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Appears to be scanned"],
            is_scanned=True,
            page_count=1,
            has_text=False,
        )

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.PDF_NOT_PROCESSABLE
        assert result.is_success is False
        assert result.warnings == ["Appears to be scanned"]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    def test_pdf_not_processable_invalid(self, mock_validate, mock_hash, extractor):
        """Test extraction with invalid PDF (not scanned)."""
        pdf_path = Path("invalid.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=False,
            errors=["No text content"],
            warnings=[],
            is_scanned=False,
            page_count=0,
            has_text=False,
        )

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.PDF_INVALID
        assert result.is_success is False
        assert result.errors == ["No text content"]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_text_extraction_fails_with_pdf_error(
        self, mock_extract_text, mock_validate, mock_hash, extractor
    ):
        """Test extraction when PDF text extraction fails with PDFProcessingError."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], is_scanned=False, has_text=True
        )
        mock_extract_text.side_effect = PDFProcessingError("Cannot extract text")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.PDF_INVALID
        assert result.is_success is False
        assert "Cannot extract text" in result.errors[0]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_text_extraction_fails_with_generic_error(
        self, mock_extract_text, mock_validate, mock_hash, extractor
    ):
        """Test extraction when text extraction fails with unexpected error."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], is_scanned=False, has_text=True
        )
        mock_extract_text.side_effect = Exception("Unexpected error")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.PDF_INVALID
        assert result.is_success is False
        assert "Text extraction failed" in result.errors[0]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_llm_extraction_fails(
        self,
        mock_extract_text,
        mock_validate,
        mock_hash,
        extractor,
        mock_llm_provider,
    ):
        """Test extraction when LLM extraction fails."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], is_scanned=False, has_text=True
        )
        mock_extract_text.return_value = "Some text"
        mock_llm_provider.extract.side_effect = LLMExtractionError("API error")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.EXTRACTION_FAILED
        assert result.is_success is False
        assert "API error" in result.errors[0]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_llm_extraction_fails_with_generic_error(
        self,
        mock_extract_text,
        mock_validate,
        mock_hash,
        extractor,
        mock_llm_provider,
    ):
        """Test extraction when LLM extraction fails with unexpected error."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], is_scanned=False, has_text=True
        )
        mock_extract_text.return_value = "Some text"
        mock_llm_provider.extract.side_effect = Exception("Unexpected LLM error")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.EXTRACTION_FAILED
        assert result.is_success is False
        assert "LLM extraction failed" in result.errors[0]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.BasicExtractionResponse")
    def test_validation_fails(
        self,
        mock_response_class,
        mock_extract_text,
        mock_validate,
        mock_hash,
        extractor,
        mock_llm_provider,
    ):
        """Test extraction when Pydantic validation fails."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], is_scanned=False, has_text=True
        )
        mock_extract_text.return_value = "Some text"
        extracted_dict = {"total_amount": -10.0}  # Invalid (negative)
        mock_llm_provider.extract.return_value = extracted_dict
        mock_response_class.side_effect = ValidationError("Amount must be positive")

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.VALIDATION_FAILED
        assert result.is_success is False
        assert "Validation error" in result.errors[0]
        # Raw data should be included for debugging
        assert result.extracted_data == extracted_dict

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_extraction_with_warnings(
        self,
        mock_extract_text,
        mock_validate,
        mock_hash,
        extractor,
        mock_llm_provider,
    ):
        """Test successful extraction includes PDF warnings."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Large file size"],
            is_scanned=False,
            has_text=True,
        )
        mock_extract_text.return_value = "Some text"
        mock_llm_provider.extract.return_value = {
            "practitioner_name": "Dr. Smith",
            "total_amount": 50.0,
        }

        result = extractor.extract_from_pdf(pdf_path)

        assert result.status == ExtractionStatus.SUCCESS
        assert result.warnings == ["Large file size"]

    @patch("medical_bill_analyzer.extraction.extractor.get_pdf_hash")
    @patch("medical_bill_analyzer.extraction.extractor.validate_pdf")
    @patch("medical_bill_analyzer.extraction.extractor.extract_text_from_pdf")
    def test_extraction_type_parameter(
        self,
        mock_extract_text,
        mock_validate,
        mock_hash,
        extractor,
        mock_llm_provider,
    ):
        """Test extraction_type parameter is passed to LLM."""
        pdf_path = Path("test.pdf")
        mock_hash.return_value = "abc123"
        mock_validate.return_value = ValidationResult(
            is_valid=True, errors=[], warnings=[], is_scanned=False, has_text=True
        )
        mock_extract_text.return_value = "Some text"
        mock_llm_provider.extract.return_value = {
            "practitioner_name": "Dr. Smith",
            "total_amount": 50.0,
        }

        result = extractor.extract_from_pdf(pdf_path, extraction_type="line_items")

        assert result.status == ExtractionStatus.SUCCESS
        mock_llm_provider.extract.assert_called_once_with("Some text", "line_items")


class TestExtractFromText:
    """Test extract_from_text method."""

    def test_extract_from_text_success(self, extractor, mock_llm_provider):
        """Test extracting from text."""
        text = "Rechnung Dr. Müller 29.49 EUR"
        mock_llm_provider.extract.return_value = {
            "practitioner_name": "Dr. Müller",
            "total_amount": 29.49,
            "currency": "EUR",
        }

        result = extractor.extract_from_text(text)

        assert result is not None
        assert result["practitioner_name"] == "Dr. Müller"
        assert result["total_amount"] == 29.49
        mock_llm_provider.extract.assert_called_once_with(text, "basic")

    def test_extract_from_text_with_extraction_type(
        self, extractor, mock_llm_provider
    ):
        """Test extract_from_text with custom extraction type."""
        text = "Some text"
        mock_llm_provider.extract.return_value = {"data": "value"}

        result = extractor.extract_from_text(text, extraction_type="line_items")

        mock_llm_provider.extract.assert_called_once_with(text, "line_items")

    def test_extract_from_text_llm_error(self, extractor, mock_llm_provider):
        """Test extract_from_text with LLM error."""
        text = "Some text"
        mock_llm_provider.extract.side_effect = LLMExtractionError("API error")

        with pytest.raises(LLMExtractionError, match="API error"):
            extractor.extract_from_text(text)

    @patch("medical_bill_analyzer.extraction.extractor.BasicExtractionResponse")
    def test_extract_from_text_validation_error(
        self, mock_response_class, extractor, mock_llm_provider
    ):
        """Test extract_from_text with validation error."""
        text = "Some text"
        mock_llm_provider.extract.return_value = {"total_amount": -10.0}
        mock_response_class.side_effect = ValidationError("Invalid")

        with pytest.raises(ValidationError, match="Invalid"):
            extractor.extract_from_text(text)
