"""Tests for file utilities."""

import pytest
from pathlib import Path

from medical_bill_analyzer.utils.file_utils import (
    calculate_file_hash,
    sanitize_filename,
    copy_file_to_storage,
    ensure_directory_exists,
)
from medical_bill_analyzer.core.exceptions import PDFProcessingError


class TestCalculateFileHash:
    """Test file hash calculation."""

    def test_hash_calculation(self, temp_dir):
        """Test calculating hash of a file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        hash1 = calculate_file_hash(test_file)
        hash2 = calculate_file_hash(test_file)

        # Hash should be consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64 hex characters

    def test_hash_different_files(self, temp_dir):
        """Test that different files have different hashes."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"

        file1.write_text("Content 1")
        file2.write_text("Content 2")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2

    def test_hash_same_content(self, temp_dir):
        """Test that files with same content have same hash."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"

        content = "Same content"
        file1.write_text(content)
        file2.write_text(content)

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 == hash2

    def test_hash_nonexistent_file(self, temp_dir):
        """Test hash calculation on non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"

        with pytest.raises(PDFProcessingError):
            calculate_file_hash(nonexistent)


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_sanitize_normal_filename(self):
        """Test sanitizing a normal filename."""
        result = sanitize_filename("document.pdf")
        assert result == "document.pdf"

    def test_sanitize_special_characters(self):
        """Test sanitizing filename with special characters."""
        result = sanitize_filename("my<file>name:test.pdf")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert result == "my_file_name_test.pdf"

    def test_sanitize_spaces(self):
        """Test sanitizing filename with leading/trailing spaces."""
        result = sanitize_filename("  filename.pdf  ")
        assert result == "filename.pdf"

    def test_sanitize_empty_filename(self):
        """Test sanitizing empty filename."""
        result = sanitize_filename("")
        assert result == "unnamed"

    def test_sanitize_long_filename(self):
        """Test sanitizing very long filename."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255


class TestCopyFileToStorage:
    """Test copying files to storage."""

    def test_copy_file(self, temp_dir):
        """Test copying a file to storage directory."""
        source = temp_dir / "source.txt"
        source.write_text("Test content")

        storage_dir = temp_dir / "storage"

        result = copy_file_to_storage(source, storage_dir)

        assert result.exists()
        assert result.parent == storage_dir
        assert result.read_text() == "Test content"

    def test_copy_file_with_new_name(self, temp_dir):
        """Test copying file with a new name."""
        source = temp_dir / "source.txt"
        source.write_text("Test content")

        storage_dir = temp_dir / "storage"

        result = copy_file_to_storage(source, storage_dir, "newname.txt")

        assert result.name == "newname.txt"
        assert result.read_text() == "Test content"

    def test_copy_file_conflict_handling(self, temp_dir):
        """Test handling of filename conflicts."""
        source = temp_dir / "source.txt"
        source.write_text("Test content")

        storage_dir = temp_dir / "storage"
        storage_dir.mkdir()

        # Create existing file
        existing = storage_dir / "file.txt"
        existing.write_text("Existing content")

        # Copy should create file with different name
        result = copy_file_to_storage(source, storage_dir, "file.txt")

        assert result.name == "file_1.txt"  # Should append number
        assert existing.read_text() == "Existing content"  # Original unchanged
        assert result.read_text() == "Test content"

    def test_copy_creates_storage_dir(self, temp_dir):
        """Test that storage directory is created if it doesn't exist."""
        source = temp_dir / "source.txt"
        source.write_text("Test content")

        storage_dir = temp_dir / "new_storage"

        result = copy_file_to_storage(source, storage_dir)

        assert storage_dir.exists()
        assert result.exists()


class TestEnsureDirectoryExists:
    """Test directory creation."""

    def test_create_directory(self, temp_dir):
        """Test creating a new directory."""
        new_dir = temp_dir / "new_directory"

        ensure_directory_exists(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_nested_directory(self, temp_dir):
        """Test creating nested directories."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"

        ensure_directory_exists(nested_dir)

        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_existing_directory(self, temp_dir):
        """Test with existing directory (should not raise error)."""
        existing_dir = temp_dir / "existing"
        existing_dir.mkdir()

        # Should not raise error
        ensure_directory_exists(existing_dir)

        assert existing_dir.exists()
