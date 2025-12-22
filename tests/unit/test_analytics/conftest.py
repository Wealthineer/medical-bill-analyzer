"""Shared fixtures for analytics tests."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from medical_bill_analyzer.analytics.engine import AnalyticsEngine


@pytest.fixture
def mock_repository():
    """Create mock BillRepository for testing."""
    repository = Mock()
    return repository


@pytest.fixture
def analytics_engine(mock_repository):
    """Create AnalyticsEngine with mock repository."""
    return AnalyticsEngine(mock_repository)


@pytest.fixture
def sample_practitioner_data():
    """Sample practitioner statistics data from repository."""
    return [
        {
            "practitioner_name": "Dr. Schmidt",
            "practitioner_type": "Zahnarzt",
            "bill_count": 5,
            "total_amount": Decimal("500.00"),
            "average_amount": Decimal("100.00"),
            "first_visit": date(2024, 1, 15),
            "last_visit": date(2024, 11, 30),
        },
        {
            "practitioner_name": "Dr. Müller",
            "practitioner_type": "Arzt",
            "bill_count": 3,
            "total_amount": Decimal("300.00"),
            "average_amount": Decimal("100.00"),
            "first_visit": date(2024, 3, 10),
            "last_visit": date(2024, 9, 20),
        },
        {
            "practitioner_name": "Dr. Weber",
            "practitioner_type": "Arzt",
            "bill_count": 2,
            "total_amount": Decimal("150.00"),
            "average_amount": Decimal("75.00"),
            "first_visit": date(2024, 6, 1),
            "last_visit": date(2024, 8, 15),
        },
    ]


@pytest.fixture
def sample_category_data():
    """Sample category statistics data from repository."""
    return [
        {
            "category": "Zahnarzt",
            "bill_count": 5,
            "total_amount": Decimal("500.00"),
            "average_amount": Decimal("100.00"),
        },
        {
            "category": "Arzt",
            "bill_count": 5,
            "total_amount": Decimal("450.00"),
            "average_amount": Decimal("90.00"),
        },
        {
            "category": "Unknown",
            "bill_count": 1,
            "total_amount": Decimal("50.00"),
            "average_amount": Decimal("50.00"),
        },
    ]


@pytest.fixture
def sample_monthly_data():
    """Sample monthly statistics data from repository."""
    return [
        {
            "year": 2024,
            "month": 1,
            "bill_count": 3,
            "total_amount": Decimal("250.00"),
            "average_amount": Decimal("83.33"),
        },
        {
            "year": 2024,
            "month": 2,
            "bill_count": 2,
            "total_amount": Decimal("200.00"),
            "average_amount": Decimal("100.00"),
        },
        {
            "year": 2024,
            "month": 3,
            "bill_count": 5,
            "total_amount": Decimal("550.00"),
            "average_amount": Decimal("110.00"),
        },
    ]
