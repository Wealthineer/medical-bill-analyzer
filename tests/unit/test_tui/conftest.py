"""Fixtures for TUI tests."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch, MagicMock

import pytest

from medical_bill_analyzer.database.models import Bill, BillFilter


@pytest.fixture
def mock_settings():
    """Create mock settings object."""
    settings = Mock()
    settings.llm.provider = "anthropic"
    settings.llm.anthropic.model = "claude-sonnet-4-20250514"
    settings.llm.get_provider_config = Mock(return_value={"model": "claude-sonnet-4-20250514"})
    settings.storage.database_path = "/tmp/test.db"
    settings.storage.pdf_storage_path = "/tmp/pdfs/"
    settings.bonus.default_threshold = 1000
    return settings


@pytest.fixture
def mock_bill_repository():
    """Create mock BillRepository."""
    repository = Mock()
    repository.get_all = Mock(return_value=[])
    repository.filter = Mock(return_value=[])
    repository.delete = Mock(return_value=True)
    repository.create = Mock()
    return repository


@pytest.fixture
def sample_bills():
    """Create sample bills for testing."""
    return [
        Bill(
            id=1,
            filename="bill1.pdf",
            file_hash="a" * 64,
            pdf_path="/tmp/bill1.pdf",
            practitioner_name="Dr. Schmidt",
            practitioner_type="Arzt",
            bill_date=date(2025, 1, 15),
            bill_number="INV-2025-001",
            total_amount=Decimal("150.00"),
            currency="EUR",
            extraction_status="success",
            created_at=None,
            updated_at=None,
        ),
        Bill(
            id=2,
            filename="bill2.pdf",
            file_hash="b" * 64,
            pdf_path="/tmp/bill2.pdf",
            practitioner_name="Dr. Müller",
            practitioner_type="Zahnarzt",
            bill_date=date(2025, 2, 20),
            bill_number="INV-2025-002",
            total_amount=Decimal("250.00"),
            currency="EUR",
            extraction_status="success",
            created_at=None,
            updated_at=None,
        ),
        Bill(
            id=3,
            filename="bill3.pdf",
            file_hash="c" * 64,
            pdf_path="/tmp/bill3.pdf",
            practitioner_name="Dr. Weber",
            practitioner_type="Arzt",
            bill_date=date(2024, 12, 10),
            bill_number="INV-2024-003",
            total_amount=Decimal("75.00"),
            currency="EUR",
            extraction_status="needs_review",
            created_at=None,
            updated_at=None,
        ),
    ]


@pytest.fixture
def mock_bonus_calculator():
    """Create mock BonusCalculator."""
    calculator = Mock()
    calculator.calculate_total = Mock(return_value=Decimal("400.00"))

    recommendation = Mock()
    recommendation.should_keep_bonus = True
    recommendation.threshold = Decimal("1000.00")
    recommendation.total_amount = Decimal("400.00")
    recommendation.savings = Decimal("600.00")
    recommendation.explanation = "Keep your bonus"

    calculator.get_recommendation_for_year = Mock(return_value=recommendation)
    return calculator


@pytest.fixture
def mock_analytics_engine():
    """Create mock AnalyticsEngine."""
    from medical_bill_analyzer.analytics.models import PractitionerStats

    engine = Mock()
    engine.get_practitioner_stats = Mock(return_value=[
        PractitionerStats(
            practitioner_name="Dr. Schmidt",
            practitioner_type="Arzt",
            bill_count=3,
            total_amount=Decimal("450.00"),
            average_amount=Decimal("150.00"),
            first_visit=date(2024, 1, 1),
            last_visit=date(2025, 1, 15),
        ),
    ])
    engine.get_category_stats = Mock(return_value=[])
    engine.get_monthly_stats = Mock(return_value=[])
    return engine


@pytest.fixture
def mock_load_config(mock_settings):
    """Patch load_config to return mock settings."""
    with patch("medical_bill_analyzer.cli.utils.load_config", return_value=mock_settings):
        yield mock_settings


@pytest.fixture
def mock_get_database_path():
    """Patch get_database_path."""
    with patch(
        "medical_bill_analyzer.cli.utils.get_database_path",
        return_value=Path("/tmp/test.db")
    ):
        yield


@pytest.fixture
def temp_pdf_file(tmp_path):
    """Create a temporary PDF file for testing."""
    pdf_path = tmp_path / "test_bill.pdf"
    # Create a minimal PDF file
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    return pdf_path
