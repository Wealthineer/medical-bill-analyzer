"""Tests for PDF validation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from medical_bill_analyzer.core.exceptions import PDFProcessingError
from medical_bill_analyzer.pdf.validator import (
    MIN_TEXT_LENGTH,
    ValidationResult,
    is_scanned_pdf,
    validate_pdf,
)


class TestValidatePDF:
    """Test validate_pdf function."""

    def test_file_not_found(self, temp_dir):
        """Test validation of non-existent file."""
        pdf_path = temp_dir / "nonexistent.pdf"

        result = validate_pdf(pdf_path)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_path_is_directory(self, temp_dir):
        """Test validation of directory path."""
        result = validate_pdf(temp_dir)

        assert not result.is_valid
        assert "not a file" in result.errors[0].lower()

    def test_empty_file(self, temp_dir):
        """Test validation of empty PDF file."""
        pdf_path = temp_dir / "empty.pdf"
        pdf_path.touch()  # Create empty file

        result = validate_pdf(pdf_path)

        assert not result.is_valid
        assert "empty" in result.errors[0].lower()
        assert result.file_size_bytes == 0

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_valid_pdf_with_text(self, mock_pdfplumber, temp_dir):
        """Test validation of valid PDF with text."""
        pdf_path = temp_dir / "valid.pdf"
        pdf_path.write_text("dummy content")  # Non-zero size

        # Mock PDF with text
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * (MIN_TEXT_LENGTH + 10)

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = validate_pdf(pdf_path)

        assert result.is_valid
        assert result.has_text
        assert not result.is_scanned
        assert result.page_count == 1
        assert result.is_processable
        assert len(result.errors) == 0

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_scanned_pdf_minimal_text(self, mock_pdfplumber, temp_dir):
        """Test validation of scanned PDF (minimal text)."""
        pdf_path = temp_dir / "scanned.pdf"
        pdf_path.write_text("dummy content")

        # Mock PDF with very little text (< MIN_TEXT_LENGTH)
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "AB"  # Only 2 characters

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = validate_pdf(pdf_path)

        assert result.is_valid  # Valid PDF structure
        assert not result.has_text
        assert result.is_scanned
        assert not result.is_processable  # Can't process scanned PDFs
        assert len(result.warnings) > 0
        assert "scanned" in result.warnings[0].lower()

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_pdf_no_pages(self, mock_pdfplumber, temp_dir):
        """Test validation of PDF with no pages."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_text("dummy content")

        mock_pdf = MagicMock()
        mock_pdf.pages = []

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = validate_pdf(pdf_path)

        assert not result.is_valid
        assert "no pages" in result.errors[0].lower()
        assert result.page_count == 0

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_corrupted_pdf(self, mock_pdfplumber, temp_dir):
        """Test validation of corrupted PDF."""
        pdf_path = temp_dir / "corrupted.pdf"
        pdf_path.write_text("dummy content")

        from pdfminer.pdfparser import PDFSyntaxError

        mock_pdfplumber.open.side_effect = PDFSyntaxError("Invalid")

        result = validate_pdf(pdf_path)

        assert not result.is_valid
        assert any("corrupted" in err.lower() for err in result.errors)

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_password_protected_pdf(self, mock_pdfplumber, temp_dir):
        """Test validation of password-protected PDF."""
        pdf_path = temp_dir / "protected.pdf"
        pdf_path.write_text("dummy content")

        from pdfminer.pdfdocument import PDFPasswordIncorrect

        mock_pdfplumber.open.side_effect = PDFPasswordIncorrect("Password")

        result = validate_pdf(pdf_path)

        assert not result.is_valid
        assert any("password" in err.lower() for err in result.errors)

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_large_pdf_warning(self, mock_pdfplumber, temp_dir):
        """Test warning for large PDF files."""
        pdf_path = temp_dir / "large.pdf"
        # Create file larger than MAX_FILE_SIZE
        large_size = 101 * 1024 * 1024  # 101 MB
        pdf_path.write_bytes(b"0" * large_size)

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * (MIN_TEXT_LENGTH + 10)

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = validate_pdf(pdf_path)

        assert result.is_valid  # Still valid, just large
        assert len(result.warnings) > 0
        assert any("large" in warn.lower() for warn in result.warnings)
        assert result.file_size_bytes == large_size

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_multi_page_pdf(self, mock_pdfplumber, temp_dir):
        """Test validation of multi-page PDF."""
        pdf_path = temp_dir / "multipage.pdf"
        pdf_path.write_text("dummy content")

        # Mock 3-page PDF
        mock_pages = []
        for _ in range(3):
            page = MagicMock()
            page.extract_text.return_value = "Page content " * 20
            mock_pages.append(page)

        mock_pdf = MagicMock()
        mock_pdf.pages = mock_pages

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        result = validate_pdf(pdf_path)

        assert result.is_valid
        assert result.page_count == 3
        assert result.has_text

    @patch("medical_bill_analyzer.pdf.validator.pdfplumber")
    def test_generic_error(self, mock_pdfplumber, temp_dir):
        """Test validation handles generic errors."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_text("dummy content")

        mock_pdfplumber.open.side_effect = Exception("Unknown error")

        result = validate_pdf(pdf_path)

        assert not result.is_valid
        assert len(result.errors) > 0


class TestIsScannnedPDF:
    """Test is_scanned_pdf function."""

    @patch("medical_bill_analyzer.pdf.validator.validate_pdf")
    def test_scanned_pdf_returns_true(self, mock_validate):
        """Test is_scanned_pdf returns True for scanned PDF."""
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=["Scanned PDF"],
            is_scanned=True,
            page_count=1,
            has_text=False,
            file_size_bytes=1000,
        )

        result = is_scanned_pdf(Path("test.pdf"))

        assert result is True

    @patch("medical_bill_analyzer.pdf.validator.validate_pdf")
    def test_text_pdf_returns_false(self, mock_validate):
        """Test is_scanned_pdf returns False for text PDF."""
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            is_scanned=False,
            page_count=1,
            has_text=True,
            file_size_bytes=1000,
        )

        result = is_scanned_pdf(Path("test.pdf"))

        assert result is False

    @patch("medical_bill_analyzer.pdf.validator.validate_pdf")
    def test_invalid_pdf_raises_error(self, mock_validate):
        """Test is_scanned_pdf raises error for invalid PDF."""
        mock_validate.return_value = ValidationResult(
            is_valid=False,
            errors=["PDF is corrupted"],
            warnings=[],
            is_scanned=False,
            page_count=0,
            has_text=False,
            file_size_bytes=0,
        )

        with pytest.raises(PDFProcessingError) as exc:
            is_scanned_pdf(Path("test.pdf"))

        assert "corrupted" in str(exc.value).lower()


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_is_processable_true(self):
        """Test is_processable returns True for valid, text PDF."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            is_scanned=False,
            page_count=1,
            has_text=True,
            file_size_bytes=1000,
        )

        assert result.is_processable is True

    def test_is_processable_false_scanned(self):
        """Test is_processable returns False for scanned PDF."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            is_scanned=True,
            page_count=1,
            has_text=False,
            file_size_bytes=1000,
        )

        assert result.is_processable is False

    def test_is_processable_false_invalid(self):
        """Test is_processable returns False for invalid PDF."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error"],
            warnings=[],
            is_scanned=False,
            page_count=0,
            has_text=False,
            file_size_bytes=0,
        )

        assert result.is_processable is False

    def test_is_processable_false_no_text(self):
        """Test is_processable returns False for PDF without text."""
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            is_scanned=False,
            page_count=1,
            has_text=False,  # No text
            file_size_bytes=1000,
        )

        assert result.is_processable is False
