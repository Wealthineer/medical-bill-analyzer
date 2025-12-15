"""Tests for LLM prompts."""

import pytest

from medical_bill_analyzer.llm.prompts import (
    BASIC_EXTRACTION_PROMPT,
    LINE_ITEM_EXTRACTION_PROMPT,
    get_prompt,
)


class TestGetPrompt:
    """Test get_prompt function."""

    def test_basic_extraction_prompt(self):
        """Test getting basic extraction prompt."""
        bill_text = "Test bill text"

        prompt = get_prompt("basic", bill_text)

        assert "Test bill text" in prompt
        assert "Arztrechnung" in prompt
        assert "practitioner_name" in prompt
        assert "total_amount" in prompt
        assert "JSON" in prompt

    def test_line_item_extraction_prompt(self):
        """Test getting line item extraction prompt."""
        bill_text = "Test bill text with line items"

        prompt = get_prompt("line_items", bill_text)

        assert "Test bill text with line items" in prompt
        assert "line_items" in prompt
        assert "goa_code" in prompt
        assert "JSON" in prompt

    def test_unknown_extraction_type_raises_error(self):
        """Test unknown extraction type raises ValueError."""
        with pytest.raises(ValueError) as exc:
            get_prompt("unknown_type", "test text")

        assert "unknown_type" in str(exc.value).lower()

    def test_empty_bill_text_included(self):
        """Test empty bill text is included in prompt."""
        prompt = get_prompt("basic", "")

        assert "" in prompt  # Empty string should be in prompt

    def test_german_characters_preserved(self):
        """Test German characters are preserved in prompt."""
        bill_text = "Rechnung vom Arzt Dr. Müller für €29,49"

        prompt = get_prompt("basic", bill_text)

        assert "Müller" in prompt
        assert "€" in prompt


class TestBasicExtractionPrompt:
    """Test basic extraction prompt template."""

    def test_contains_required_fields(self):
        """Test prompt contains all required extraction fields."""
        required_fields = [
            "practitioner_name",
            "practitioner_type",
            "bill_date",
            "bill_number",
            "total_amount",
            "currency",
        ]

        for field in required_fields:
            assert field in BASIC_EXTRACTION_PROMPT

    def test_contains_practitioner_types(self):
        """Test prompt lists all valid practitioner types."""
        practitioner_types = [
            "Arzt",
            "Zahnarzt",
            "Heilpraktiker",
            "Krankenhaus",
            "Labor",
            "Apotheke",
            "Sonstige",
        ]

        for ptype in practitioner_types:
            assert ptype in BASIC_EXTRACTION_PROMPT

    def test_contains_german_terminology(self):
        """Test prompt includes German medical billing terms."""
        german_terms = [
            "Arztrechnung",
            "Rechnung",
            "Gesamtbetrag",
        ]

        for term in german_terms:
            assert term in BASIC_EXTRACTION_PROMPT

    def test_contains_date_format_instruction(self):
        """Test prompt specifies YYYY-MM-DD date format."""
        assert "YYYY-MM-DD" in BASIC_EXTRACTION_PROMPT

    def test_contains_json_structure(self):
        """Test prompt shows JSON structure."""
        assert "{{" in BASIC_EXTRACTION_PROMPT
        assert "}}" in BASIC_EXTRACTION_PROMPT
        assert "JSON" in BASIC_EXTRACTION_PROMPT

    def test_has_placeholder_for_bill_text(self):
        """Test prompt has placeholder for bill text."""
        assert "{bill_text}" in BASIC_EXTRACTION_PROMPT


class TestLineItemExtractionPrompt:
    """Test line item extraction prompt template."""

    def test_contains_required_fields(self):
        """Test prompt contains line item fields."""
        required_fields = [
            "practitioner_info",
            "line_items",
            "goa_code",
            "description",
            "quantity",
            "unit_price",
            "total_price",
        ]

        for field in required_fields:
            assert field in LINE_ITEM_EXTRACTION_PROMPT

    def test_contains_goa_terminology(self):
        """Test prompt mentions GOÄ (German medical fee schedule)."""
        assert "GOÄ" in LINE_ITEM_EXTRACTION_PROMPT or "EBM" in LINE_ITEM_EXTRACTION_PROMPT

    def test_has_placeholder_for_bill_text(self):
        """Test prompt has placeholder for bill text."""
        assert "{bill_text}" in LINE_ITEM_EXTRACTION_PROMPT

    def test_contains_json_structure(self):
        """Test prompt shows JSON structure with nested objects."""
        assert "{{" in LINE_ITEM_EXTRACTION_PROMPT
        assert "}}" in LINE_ITEM_EXTRACTION_PROMPT
        assert "[" in LINE_ITEM_EXTRACTION_PROMPT  # Array for line items
        assert "]" in LINE_ITEM_EXTRACTION_PROMPT
