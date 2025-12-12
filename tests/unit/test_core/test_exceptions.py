"""Tests for custom exceptions."""

import pytest

from medical_bill_analyzer.core.exceptions import (
    MedicalBillAnalyzerError,
    ConfigError,
    PDFProcessingError,
    LLMExtractionError,
    DatabaseError,
    ValidationError,
    DuplicateBillError,
    ProviderNotAvailableError,
)


class TestExceptions:
    """Test custom exception hierarchy."""

    def test_base_exception(self):
        """Test base exception."""
        error = MedicalBillAnalyzerError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_config_error(self):
        """Test ConfigError."""
        error = ConfigError("Config error")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_pdf_processing_error(self):
        """Test PDFProcessingError."""
        error = PDFProcessingError("PDF error")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_llm_extraction_error(self):
        """Test LLMExtractionError."""
        error = LLMExtractionError("Extraction error")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_database_error(self):
        """Test DatabaseError."""
        error = DatabaseError("Database error")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Validation error")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_duplicate_bill_error(self):
        """Test DuplicateBillError."""
        error = DuplicateBillError("Duplicate bill")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_provider_not_available_error(self):
        """Test ProviderNotAvailableError."""
        error = ProviderNotAvailableError("Provider unavailable")
        assert isinstance(error, MedicalBillAnalyzerError)

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(PDFProcessingError):
            raise PDFProcessingError("Test")

    def test_exception_inheritance(self):
        """Test exception inheritance."""
        try:
            raise ConfigError("Test")
        except MedicalBillAnalyzerError:
            pass  # Should be caught as base exception
        else:
            pytest.fail("Exception not caught by base class")
