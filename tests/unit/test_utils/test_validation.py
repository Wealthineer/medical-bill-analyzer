"""Tests for validation utilities."""

import pytest
from datetime import date
from decimal import Decimal

from medical_bill_analyzer.utils.validation import (
    validate_amount,
    validate_date,
    validate_practitioner_type,
    VALID_PRACTITIONER_TYPES,
)
from medical_bill_analyzer.core.exceptions import ValidationError


class TestValidateAmount:
    """Test amount validation."""

    def test_valid_positive_amount(self):
        """Test valid positive amount."""
        assert validate_amount(Decimal("100.50")) is True

    def test_valid_positive_float(self):
        """Test valid positive float."""
        assert validate_amount(100.50) is True

    def test_invalid_zero_default(self):
        """Test that zero is invalid by default."""
        with pytest.raises(ValidationError):
            validate_amount(Decimal("0"))

    def test_valid_zero_when_allowed(self):
        """Test that zero is valid when allowed."""
        assert validate_amount(Decimal("0"), allow_zero=True) is True

    def test_invalid_negative(self):
        """Test that negative is invalid."""
        with pytest.raises(ValidationError):
            validate_amount(Decimal("-100"))

    def test_invalid_none(self):
        """Test that None is invalid."""
        assert validate_amount(None) is False


class TestValidateDate:
    """Test date validation."""

    def test_valid_past_date(self):
        """Test valid date in the past."""
        past_date = date(2020, 1, 1)
        assert validate_date(past_date) is True

    def test_invalid_future_date_default(self):
        """Test that future date is invalid by default."""
        future_date = date(2030, 1, 1)
        with pytest.raises(ValidationError):
            validate_date(future_date)

    def test_valid_future_date_when_allowed(self):
        """Test that future date is valid when allowed."""
        future_date = date(2030, 1, 1)
        assert validate_date(future_date, require_past=False, allow_future=True) is True

    def test_invalid_today_when_past_required(self):
        """Test that today is invalid when past required."""
        today = date.today()
        with pytest.raises(ValidationError):
            validate_date(today, require_past=True)

    def test_valid_today_when_not_past_required(self):
        """Test that today is valid when past not required."""
        today = date.today()
        assert validate_date(today, require_past=False) is True

    def test_invalid_none(self):
        """Test that None is invalid."""
        assert validate_date(None) is False


class TestValidatePractitionerType:
    """Test practitioner type validation."""

    def test_valid_arzt(self):
        """Test valid 'Arzt' type."""
        assert validate_practitioner_type("Arzt") is True

    def test_valid_zahnarzt(self):
        """Test valid 'Zahnarzt' type."""
        assert validate_practitioner_type("Zahnarzt") is True

    def test_valid_all_types(self):
        """Test all valid types."""
        for practitioner_type in VALID_PRACTITIONER_TYPES:
            assert validate_practitioner_type(practitioner_type) is True

    def test_invalid_type(self):
        """Test invalid practitioner type."""
        with pytest.raises(ValidationError):
            validate_practitioner_type("InvalidType")

    def test_invalid_none(self):
        """Test that None is invalid."""
        assert validate_practitioner_type(None) is False

    def test_invalid_empty_string(self):
        """Test that empty string is invalid."""
        with pytest.raises(ValidationError):
            validate_practitioner_type("")

    def test_case_sensitive(self):
        """Test that validation is case-sensitive."""
        with pytest.raises(ValidationError):
            validate_practitioner_type("arzt")  # lowercase
