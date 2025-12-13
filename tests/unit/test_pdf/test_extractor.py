"""Tests for PDF text extraction."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from medical_bill_analyzer.core.exceptions import PDFProcessingError
from medical_bill_analyzer.pdf.extractor import extract_text_from_pdf


class TestExtractTextFromPDF:
    """Test extract_text_from_pdf function."""

    def test_file_not_found(self, temp_dir):
        """Test extraction from non-existent file raises error."""
        pdf_path = temp_dir / "nonexistent.pdf"

        with pytest.raises(PDFProcessingError) as exc:
            extract_text_from_pdf(pdf_path)

        assert "not found" in str(exc.value).lower()

    def test_path_is_not_file(self, temp_dir):
        """Test extraction from directory raises error."""
        with pytest.raises(PDFProcessingError) as exc:
            extract_text_from_pdf(temp_dir)

        assert "not a file" in str(exc.value).lower()

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_extract_single_page(self, mock_pdfplumber, temp_dir):
        """Test extracting text from single-page PDF."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        # Mock PDF with single page
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test PDF content"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        text = extract_text_from_pdf(pdf_path)

        assert text == "Test PDF content"
        mock_page.extract_text.assert_called_once()

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_extract_multi_page(self, mock_pdfplumber, temp_dir):
        """Test extracting text from multi-page PDF."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        # Mock PDF with three pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3 content"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        text = extract_text_from_pdf(pdf_path)

        # Pages should be joined with double newlines
        expected = "Page 1 content\n\nPage 2 content\n\nPage 3 content"
        assert text == expected

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_empty_pages_skipped(self, mock_pdfplumber, temp_dir):
        """Test that empty pages are handled gracefully."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        # Mock PDF with some empty pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page

        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3 content"

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        text = extract_text_from_pdf(pdf_path)

        # Empty page should be skipped
        expected = "Page 1 content\n\nPage 3 content"
        assert text == expected

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_pdf_no_pages(self, mock_pdfplumber, temp_dir):
        """Test PDF with no pages raises error."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        mock_pdf = MagicMock()
        mock_pdf.pages = []

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        with pytest.raises(PDFProcessingError) as exc:
            extract_text_from_pdf(pdf_path)

        assert "no pages" in str(exc.value).lower()

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_pdf_no_text(self, mock_pdfplumber, temp_dir):
        """Test PDF with no text returns empty string."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        # All pages return empty or None
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = ""

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        text = extract_text_from_pdf(pdf_path)

        assert text == ""

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_corrupted_pdf(self, mock_pdfplumber, temp_dir):
        """Test corrupted PDF raises specific error."""
        pdf_path = temp_dir / "corrupted.pdf"
        pdf_path.touch()

        # Simulate PDF syntax error
        from pdfminer.pdfparser import PDFSyntaxError

        mock_pdfplumber.open.side_effect = PDFSyntaxError("Invalid PDF")

        with pytest.raises(PDFProcessingError) as exc:
            extract_text_from_pdf(pdf_path)

        assert "corrupted" in str(exc.value).lower()

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_password_protected_pdf(self, mock_pdfplumber, temp_dir):
        """Test password-protected PDF raises specific error."""
        pdf_path = temp_dir / "protected.pdf"
        pdf_path.touch()

        # Simulate password error
        from pdfminer.pdfdocument import PDFPasswordIncorrect

        mock_pdfplumber.open.side_effect = PDFPasswordIncorrect("Password required")

        with pytest.raises(PDFProcessingError) as exc:
            extract_text_from_pdf(pdf_path)

        assert "password" in str(exc.value).lower()

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_generic_error(self, mock_pdfplumber, temp_dir):
        """Test generic error is wrapped in PDFProcessingError."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        mock_pdfplumber.open.side_effect = Exception("Unknown error")

        with pytest.raises(PDFProcessingError) as exc:
            extract_text_from_pdf(pdf_path)

        assert "failed to extract" in str(exc.value).lower()

    @patch("medical_bill_analyzer.pdf.extractor.pdfplumber")
    def test_whitespace_only_text(self, mock_pdfplumber, temp_dir):
        """Test PDF with only whitespace returns empty string."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.touch()

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "   \n\n\t  "

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        text = extract_text_from_pdf(pdf_path)

        # Whitespace-only should return empty string
        assert text == ""
