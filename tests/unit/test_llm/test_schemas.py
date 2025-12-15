"""Tests for LLM response schemas."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from medical_bill_analyzer.llm.schemas import BasicExtractionResponse, ExtractionError


class TestBasicExtractionResponse:
    """Test BasicExtractionResponse schema."""

    def test_valid_complete_response(self):
        """Test valid response with all fields populated."""
        data = {
            "practitioner_name": "Dr. med. Anna Müller",
            "practitioner_type": "Arzt",
            "bill_date": "2024-03-15",
            "bill_number": "2024-001234",
            "total_amount": 29.49,
            "currency": "EUR",
        }

        response = BasicExtractionResponse(**data)

        assert response.practitioner_name == "Dr. med. Anna Müller"
        assert response.practitioner_type == "Arzt"
        assert response.bill_date == date(2024, 3, 15)
        assert response.bill_number == "2024-001234"
        assert response.total_amount == 29.49
        assert response.currency == "EUR"

    def test_valid_minimal_response(self):
        """Test valid response with only required fields (all optional)."""
        data = {}

        response = BasicExtractionResponse(**data)

        assert response.practitioner_name is None
        assert response.practitioner_type is None
        assert response.bill_date is None
        assert response.bill_number is None
        assert response.total_amount is None
        assert response.currency == "EUR"  # Has default

    def test_valid_practitioner_types(self):
        """Test all valid practitioner types."""
        valid_types = [
            "Arzt",
            "Zahnarzt",
            "Heilpraktiker",
            "Krankenhaus",
            "Labor",
            "Apotheke",
            "Sonstige",
        ]

        for practitioner_type in valid_types:
            data = {"practitioner_type": practitioner_type}
            response = BasicExtractionResponse(**data)
            assert response.practitioner_type == practitioner_type

    def test_invalid_practitioner_type(self):
        """Test invalid practitioner type raises error."""
        data = {"practitioner_type": "InvalidType"}

        with pytest.raises(ValidationError) as exc:
            BasicExtractionResponse(**data)

        assert "practitioner_type" in str(exc.value)

    def test_valid_date_formats(self):
        """Test various date formats are accepted."""
        # ISO format string
        response = BasicExtractionResponse(bill_date="2024-03-15")
        assert response.bill_date == date(2024, 3, 15)

        # date object
        response = BasicExtractionResponse(bill_date=date(2024, 3, 15))
        assert response.bill_date == date(2024, 3, 15)

    def test_future_date_rejected(self):
        """Test that future dates are rejected."""
        tomorrow = date.today() + timedelta(days=1)
        data = {"bill_date": tomorrow}

        with pytest.raises(ValidationError) as exc:
            BasicExtractionResponse(**data)

        assert "future" in str(exc.value).lower()

    def test_today_date_accepted(self):
        """Test that today's date is accepted."""
        data = {"bill_date": date.today()}

        response = BasicExtractionResponse(**data)
        assert response.bill_date == date.today()

    def test_past_date_accepted(self):
        """Test that past dates are accepted."""
        yesterday = date.today() - timedelta(days=1)
        data = {"bill_date": yesterday}

        response = BasicExtractionResponse(**data)
        assert response.bill_date == yesterday

    def test_positive_amount_required(self):
        """Test that amount must be positive."""
        data = {"total_amount": -10.00}

        with pytest.raises(ValidationError) as exc:
            BasicExtractionResponse(**data)

        assert "total_amount" in str(exc.value)

    def test_zero_amount_rejected(self):
        """Test that zero amount is rejected."""
        data = {"total_amount": 0}

        with pytest.raises(ValidationError) as exc:
            BasicExtractionResponse(**data)

        assert "total_amount" in str(exc.value)

    def test_positive_amounts_accepted(self):
        """Test various positive amounts."""
        amounts = [0.01, 1.00, 29.49, 150.00, 1234.56, 9999.99]

        for amount in amounts:
            data = {"total_amount": amount}
            response = BasicExtractionResponse(**data)
            assert response.total_amount == amount

    def test_currency_defaults_to_eur(self):
        """Test currency defaults to EUR."""
        data = {"total_amount": 10.00}

        response = BasicExtractionResponse(**data)
        assert response.currency == "EUR"

    def test_currency_must_be_eur(self):
        """Test non-EUR currency is rejected."""
        data = {"currency": "USD"}

        with pytest.raises(ValidationError) as exc:
            BasicExtractionResponse(**data)

        assert "currency" in str(exc.value)

    def test_german_characters_in_names(self):
        """Test German umlauts and special characters are preserved."""
        data = {
            "practitioner_name": "Dr. Müller-Schäfer & Söhne GmbH",
        }

        response = BasicExtractionResponse(**data)
        assert response.practitioner_name == "Dr. Müller-Schäfer & Söhne GmbH"

    def test_bill_number_formats(self):
        """Test various bill number formats."""
        bill_numbers = [
            "2024-001234",
            "RN-12345",
            "Invoice 123",
            "001",
            "A/B/C-123-456",
        ]

        for bill_number in bill_numbers:
            data = {"bill_number": bill_number}
            response = BasicExtractionResponse(**data)
            assert response.bill_number == bill_number


class TestExtractionError:
    """Test ExtractionError schema."""

    def test_valid_error(self):
        """Test valid error with all fields."""
        data = {
            "error_type": "parsing_error",
            "message": "Failed to parse JSON",
            "details": "Unexpected token at position 10",
        }

        error = ExtractionError(**data)

        assert error.error_type == "parsing_error"
        assert error.message == "Failed to parse JSON"
        assert error.details == "Unexpected token at position 10"

    def test_error_without_details(self):
        """Test error without optional details field."""
        data = {
            "error_type": "api_error",
            "message": "API connection failed",
        }

        error = ExtractionError(**data)

        assert error.error_type == "api_error"
        assert error.message == "API connection failed"
        assert error.details is None

    def test_error_types(self):
        """Test various error types."""
        error_types = ["parsing_error", "validation_error", "api_error", "timeout"]

        for error_type in error_types:
            data = {"error_type": error_type, "message": "Test error"}
            error = ExtractionError(**data)
            assert error.error_type == error_type
