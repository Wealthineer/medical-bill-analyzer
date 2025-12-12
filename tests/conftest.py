"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import date
from decimal import Decimal


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        "llm": {
            "provider": "anthropic",
            "anthropic": {
                "model": "claude-sonnet-4-20250514",
                "api_key_env": "ANTHROPIC_API_KEY",
                "max_tokens": 1000,
                "temperature": 0,
            },
            "openai": {
                "model": "gpt-4o-mini",
                "api_key_env": "OPENAI_API_KEY",
                "max_tokens": 1000,
                "temperature": 0,
            },
            "ollama": {
                "host": "http://localhost:11434",
                "model": "llama3.1:8b",
                "timeout": 60,
            },
        },
        "storage": {
            "database_path": "./data/medical_bills.db",
            "pdf_storage_path": "./data/pdfs/",
        },
        "bonus": {
            "default_threshold": 1000,
        },
        "extraction": {
            "retry_attempts": 1,
            "extract_line_items": False,
        },
    }


@pytest.fixture
def sample_bill_data():
    """Sample bill data for testing."""
    return {
        "practitioner_name": "Dr. Schmidt",
        "practitioner_type": "Arzt",
        "bill_date": date(2024, 12, 1),
        "bill_number": "INV-2024-001",
        "total_amount": Decimal("120.50"),
        "currency": "EUR",
    }


@pytest.fixture
def sample_pdf_text():
    """Sample PDF text for testing extraction."""
    return """
    Dr. med. Schmidt
    Facharzt für Allgemeinmedizin

    Rechnung Nr.: INV-2024-001
    Datum: 01.12.2024

    Leistungen:
    1. Beratung - GOÄ 1 - 2,3-fach - 10,72 EUR
    2. Untersuchung - GOÄ 5 - 2,3-fach - 12,50 EUR

    Gesamtbetrag: 120,50 EUR
    """
