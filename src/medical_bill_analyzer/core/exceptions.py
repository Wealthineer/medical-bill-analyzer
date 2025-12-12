"""Custom exceptions for Medical Bill Analyzer."""


class MedicalBillAnalyzerError(Exception):
    """Base exception for all Medical Bill Analyzer errors."""

    pass


class ConfigError(MedicalBillAnalyzerError):
    """Raised when there's a configuration error."""

    pass


class PDFProcessingError(MedicalBillAnalyzerError):
    """Raised when PDF processing fails."""

    pass


class LLMExtractionError(MedicalBillAnalyzerError):
    """Raised when LLM extraction fails."""

    pass


class DatabaseError(MedicalBillAnalyzerError):
    """Raised when database operations fail."""

    pass


class ValidationError(MedicalBillAnalyzerError):
    """Raised when data validation fails."""

    pass


class DuplicateBillError(MedicalBillAnalyzerError):
    """Raised when attempting to add a duplicate bill."""

    pass


class ProviderNotAvailableError(MedicalBillAnalyzerError):
    """Raised when the configured LLM provider is not available."""

    pass
