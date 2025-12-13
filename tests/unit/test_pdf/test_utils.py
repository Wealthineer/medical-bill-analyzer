"""Tests for PDF utility functions."""

from pathlib import Path

import pytest

from medical_bill_analyzer.pdf.utils import get_pdf_hash, get_pdf_info


class TestGetPDFHash:
    """Test get_pdf_hash function."""

    def test_hash_calculation(self, temp_dir):
        """Test PDF hash is calculated correctly."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"PDF content")

        hash_value = get_pdf_hash(pdf_path)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex length

    def test_identical_files_same_hash(self, temp_dir):
        """Test identical PDFs have same hash."""
        content = b"PDF content for testing"

        pdf1 = temp_dir / "test1.pdf"
        pdf1.write_bytes(content)

        pdf2 = temp_dir / "test2.pdf"
        pdf2.write_bytes(content)

        hash1 = get_pdf_hash(pdf1)
        hash2 = get_pdf_hash(pdf2)

        assert hash1 == hash2

    def test_different_files_different_hash(self, temp_dir):
        """Test different PDFs have different hashes."""
        pdf1 = temp_dir / "test1.pdf"
        pdf1.write_bytes(b"PDF content 1")

        pdf2 = temp_dir / "test2.pdf"
        pdf2.write_bytes(b"PDF content 2")

        hash1 = get_pdf_hash(pdf1)
        hash2 = get_pdf_hash(pdf2)

        assert hash1 != hash2

    def test_nonexistent_file_raises_error(self, temp_dir):
        """Test hash calculation on non-existent file raises error."""
        from medical_bill_analyzer.core.exceptions import PDFProcessingError

        pdf_path = temp_dir / "nonexistent.pdf"

        with pytest.raises(PDFProcessingError) as exc:
            get_pdf_hash(pdf_path)

        assert "failed to calculate hash" in str(exc.value).lower()


class TestGetPDFInfo:
    """Test get_pdf_info function."""

    def test_basic_info(self, temp_dir):
        """Test getting basic PDF info."""
        pdf_path = temp_dir / "test.pdf"
        content = b"PDF test content"
        pdf_path.write_bytes(content)

        info = get_pdf_info(pdf_path)

        assert isinstance(info, dict)
        assert info["filename"] == "test.pdf"
        assert info["size_bytes"] == len(content)
        assert isinstance(info["size_mb"], float)
        assert isinstance(info["hash"], str)

    def test_size_calculation(self, temp_dir):
        """Test file size calculations."""
        pdf_path = temp_dir / "test.pdf"
        # Create 1 MB file
        size_bytes = 1024 * 1024
        pdf_path.write_bytes(b"0" * size_bytes)

        info = get_pdf_info(pdf_path)

        assert info["size_bytes"] == size_bytes
        assert abs(info["size_mb"] - 1.0) < 0.01  # ~1 MB

    def test_hash_included(self, temp_dir):
        """Test that hash is included in info."""
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"content")

        info = get_pdf_info(pdf_path)

        assert "hash" in info
        assert len(info["hash"]) == 64  # SHA256 hex

    def test_filename_preserved(self, temp_dir):
        """Test that original filename is preserved."""
        pdf_path = temp_dir / "my_medical_bill_2024.pdf"
        pdf_path.write_bytes(b"content")

        info = get_pdf_info(pdf_path)

        assert info["filename"] == "my_medical_bill_2024.pdf"

    def test_nonexistent_file_raises_error(self, temp_dir):
        """Test getting info on non-existent file raises error."""
        pdf_path = temp_dir / "nonexistent.pdf"

        with pytest.raises(FileNotFoundError) as exc:
            get_pdf_info(pdf_path)

        assert "not found" in str(exc.value).lower()

    def test_empty_file(self, temp_dir):
        """Test getting info on empty file."""
        pdf_path = temp_dir / "empty.pdf"
        pdf_path.touch()

        info = get_pdf_info(pdf_path)

        assert info["size_bytes"] == 0
        assert info["size_mb"] == 0.0

    def test_large_file(self, temp_dir):
        """Test getting info on large file."""
        pdf_path = temp_dir / "large.pdf"
        # Create 10 MB file
        size_bytes = 10 * 1024 * 1024
        pdf_path.write_bytes(b"0" * size_bytes)

        info = get_pdf_info(pdf_path)

        assert info["size_bytes"] == size_bytes
        assert abs(info["size_mb"] - 10.0) < 0.01  # ~10 MB
