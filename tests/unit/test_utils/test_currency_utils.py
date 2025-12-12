"""Tests for currency utilities."""

import pytest
from decimal import Decimal

from medical_bill_analyzer.utils.currency_utils import (
    format_euro,
    parse_euro,
    is_valid_amount,
)


class TestFormatEuro:
    """Test EUR formatting."""

    def test_format_with_symbol(self):
        """Test formatting with € symbol."""
        result = format_euro(Decimal("1234.56"))
        assert result == "€1.234,56"

    def test_format_without_symbol(self):
        """Test formatting without € symbol."""
        result = format_euro(Decimal("1234.56"), include_symbol=False)
        assert result == "1.234,56"

    def test_format_small_amount(self):
        """Test formatting small amount."""
        result = format_euro(Decimal("12.50"))
        assert result == "€12,50"

    def test_format_large_amount(self):
        """Test formatting large amount."""
        result = format_euro(Decimal("123456.78"))
        assert result == "€123.456,78"

    def test_format_from_float(self):
        """Test formatting from float."""
        result = format_euro(1234.56)
        assert result == "€1.234,56"

    def test_format_zero(self):
        """Test formatting zero."""
        result = format_euro(Decimal("0.00"))
        assert result == "€0,00"


class TestParseEuro:
    """Test EUR parsing."""

    def test_parse_german_format(self):
        """Test parsing German format (1.234,56)."""
        result = parse_euro("1.234,56 €")
        assert result == Decimal("1234.56")

    def test_parse_german_format_no_symbol(self):
        """Test parsing German format without symbol."""
        result = parse_euro("1.234,56")
        assert result == Decimal("1234.56")

    def test_parse_english_format(self):
        """Test parsing English format (1,234.56)."""
        result = parse_euro("1,234.56")
        assert result == Decimal("1234.56")

    def test_parse_simple_decimal(self):
        """Test parsing simple decimal."""
        result = parse_euro("€12,50")
        assert result == Decimal("12.50")

    def test_parse_with_eur(self):
        """Test parsing with EUR text."""
        result = parse_euro("100 EUR")
        assert result == Decimal("100")

    def test_parse_only_comma(self):
        """Test parsing with only comma as decimal separator."""
        result = parse_euro("12,50")
        assert result == Decimal("12.50")

    def test_parse_only_dot(self):
        """Test parsing with only dot as decimal separator."""
        result = parse_euro("12.50")
        assert result == Decimal("12.50")

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_euro("")
        assert result is None

    def test_parse_invalid_string(self):
        """Test parsing invalid string returns None."""
        result = parse_euro("not a number")
        assert result is None

    def test_parse_whitespace(self):
        """Test parsing handles whitespace."""
        result = parse_euro("  1.234,56  €  ")
        assert result == Decimal("1234.56")


class TestIsValidAmount:
    """Test amount validation."""

    def test_valid_positive_decimal(self):
        """Test valid positive Decimal amount."""
        assert is_valid_amount(Decimal("100.50")) is True

    def test_valid_positive_float(self):
        """Test valid positive float amount."""
        assert is_valid_amount(100.50) is True

    def test_invalid_zero(self):
        """Test that zero is invalid."""
        assert is_valid_amount(Decimal("0")) is False

    def test_invalid_negative(self):
        """Test that negative is invalid."""
        assert is_valid_amount(Decimal("-100")) is False

    def test_very_small_positive(self):
        """Test very small positive amount."""
        assert is_valid_amount(Decimal("0.01")) is True
