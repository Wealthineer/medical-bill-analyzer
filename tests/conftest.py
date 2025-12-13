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


# Database fixtures


@pytest.fixture
def test_db_path(temp_dir):
    """Create a temporary database path for testing."""
    return temp_dir / "test.db"


@pytest.fixture
def initialized_db(test_db_path):
    """Create and initialize a test database."""
    from medical_bill_analyzer.database import initialize_database

    initialize_database(test_db_path)
    return test_db_path


@pytest.fixture
def bill_repository(initialized_db):
    """Create a BillRepository instance with test database."""
    from medical_bill_analyzer.database import BillRepository

    return BillRepository(initialized_db)


@pytest.fixture
def sample_bill_create():
    """Sample BillCreate model for testing."""
    from medical_bill_analyzer.database import BillCreate

    return BillCreate(
        filename="test_bill.pdf",
        file_hash="a" * 64,
        pdf_path="/tmp/test_bill.pdf",
        practitioner_name="Dr. Schmidt",
        practitioner_type="Arzt",
        bill_date=date(2024, 12, 1),
        bill_number="INV-2024-001",
        total_amount=Decimal("120.50"),
        currency="EUR",
        extraction_status="success",
    )


@pytest.fixture
def sample_bill_create_2():
    """Second sample BillCreate for testing multiple bills."""
    from medical_bill_analyzer.database import BillCreate

    return BillCreate(
        filename="test_bill_2.pdf",
        file_hash="b" * 64,
        pdf_path="/tmp/test_bill_2.pdf",
        practitioner_name="Dr. Müller",
        practitioner_type="Zahnarzt",
        bill_date=date(2024, 11, 15),
        bill_number="INV-2024-002",
        total_amount=Decimal("250.00"),
        currency="EUR",
        extraction_status="success",
    )


@pytest.fixture
def created_bill(bill_repository, sample_bill_create):
    """Create a bill in the database and return it."""
    return bill_repository.create(sample_bill_create)
