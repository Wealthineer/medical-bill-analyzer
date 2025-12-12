"""Tests for date utilities."""

import pytest
from datetime import date

from medical_bill_analyzer.utils.date_utils import (
    parse_german_date,
    format_date,
    is_date_in_past,
    is_date_in_future,
    get_date_range_for_year,
)


class TestParseGermanDate:
    """Test German date parsing."""

    def test_parse_dd_mm_yyyy(self):
        """Test parsing DD.MM.YYYY format."""
        result = parse_german_date("25.12.2024")
        assert result == date(2024, 12, 25)

    def test_parse_dd_mm_yy(self):
        """Test parsing DD.MM.YY format (2-digit year)."""
        result = parse_german_date("25.12.24")
        assert result == date(2024, 12, 25)

    def test_parse_with_single_digits(self):
        """Test parsing with single digit day/month."""
        result = parse_german_date("1.5.2024")
        assert result == date(2024, 5, 1)

    def test_parse_iso_format(self):
        """Test parsing ISO format (YYYY-MM-DD)."""
        result = parse_german_date("2024-12-25")
        assert result == date(2024, 12, 25)

    def test_parse_slash_format(self):
        """Test parsing DD/MM/YYYY format."""
        result = parse_german_date("25/12/2024")
        assert result == date(2024, 12, 25)

    def test_parse_invalid_date(self):
        """Test parsing invalid date returns None."""
        result = parse_german_date("invalid")
        assert result is None

    def test_parse_empty_string(self):
        """Test parsing empty string returns None."""
        result = parse_german_date("")
        assert result is None

    def test_parse_invalid_values(self):
        """Test parsing with invalid date values returns None."""
        result = parse_german_date("32.13.2024")  # Invalid day and month
        assert result is None


class TestFormatDate:
    """Test date formatting."""

    def test_format_default(self):
        """Test default German format."""
        d = date(2024, 12, 25)
        result = format_date(d)
        assert result == "25.12.2024"

    def test_format_custom(self):
        """Test custom format."""
        d = date(2024, 12, 25)
        result = format_date(d, "%Y-%m-%d")
        assert result == "2024-12-25"


class TestIsDateInPast:
    """Test date past/future checking."""

    def test_date_in_past(self):
        """Test checking if date is in past."""
        past_date = date(2020, 1, 1)
        assert is_date_in_past(past_date) is True

    def test_date_today(self):
        """Test checking today's date."""
        today = date.today()
        assert is_date_in_past(today) is False

    def test_date_in_future(self):
        """Test checking if date is in future."""
        future_date = date(2030, 1, 1)
        assert is_date_in_past(future_date) is False


class TestIsDateInFuture:
    """Test future date checking."""

    def test_date_in_future(self):
        """Test checking if date is in future."""
        future_date = date(2030, 1, 1)
        assert is_date_in_future(future_date) is True

    def test_date_today(self):
        """Test checking today's date."""
        today = date.today()
        assert is_date_in_future(today) is False

    def test_date_in_past(self):
        """Test checking if date is in past."""
        past_date = date(2020, 1, 1)
        assert is_date_in_future(past_date) is False


class TestGetDateRangeForYear:
    """Test date range generation."""

    def test_get_year_range(self):
        """Test getting date range for a year."""
        start, end = get_date_range_for_year(2024)
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_get_year_range_different_year(self):
        """Test getting date range for different year."""
        start, end = get_date_range_for_year(2023)
        assert start == date(2023, 1, 1)
        assert end == date(2023, 12, 31)
