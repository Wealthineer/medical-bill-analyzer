"""Pydantic schemas for LLM response validation.

These schemas define the expected structure of data extracted from medical bills
by LLM providers. They ensure type safety and validation of extracted information.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BasicExtractionResponse(BaseModel):
    """Schema for basic information extracted from a German medical bill (Phase 1).

    This schema represents the core information needed for bill tracking and
    bonus calculation. Phase 3 will extend this with line item extraction.

    Attributes:
        practitioner_name: Full name of doctor or clinic (e.g., "Dr. med. Anna Müller")
        practitioner_type: Type of practitioner (Arzt, Zahnarzt, Heilpraktiker, etc.)
        bill_date: Date of the bill in YYYY-MM-DD format
        bill_number: Invoice/bill number if present
        total_amount: Total amount in EUR as positive decimal number
        currency: Currency code (always EUR for German bills)
    """

    practitioner_name: Optional[str] = Field(
        None,
        description="Full name of doctor or clinic",
        examples=["Dr. med. Anna Müller", "Praxis Dr. Schmidt"],
    )

    practitioner_type: Optional[str] = Field(
        None,
        description="Type of medical practitioner",
        pattern="^(Arzt|Zahnarzt|Heilpraktiker|Krankenhaus|Labor|Apotheke|Sonstige)$",
    )

    bill_date: Optional[date] = Field(
        None,
        description="Date of the bill",
        examples=["2024-03-15"],
    )

    bill_number: Optional[str] = Field(
        None,
        description="Invoice or bill number",
        examples=["2024-001234", "RN-12345"],
    )

    total_amount: Optional[float] = Field(
        None,
        description="Total amount in EUR",
        gt=0,
        examples=[29.49, 150.00, 1234.56],
    )

    currency: str = Field(
        default="EUR",
        description="Currency code",
        pattern="^EUR$",
    )

    @field_validator("practitioner_type")
    @classmethod
    def validate_practitioner_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate practitioner type is in allowed list."""
        if v is None:
            return v

        allowed_types = {
            "Arzt",
            "Zahnarzt",
            "Heilpraktiker",
            "Krankenhaus",
            "Labor",
            "Apotheke",
            "Sonstige",
        }

        if v not in allowed_types:
            raise ValueError(
                f"Invalid practitioner type: {v}. "
                f"Must be one of: {', '.join(sorted(allowed_types))}"
            )

        return v

    @field_validator("bill_date")
    @classmethod
    def validate_bill_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate bill date is not in the future."""
        if v is None:
            return v

        from datetime import date as dt_date

        today = dt_date.today()
        if v > today:
            raise ValueError(f"Bill date cannot be in the future: {v}")

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "practitioner_name": "Dr. med. Anna Müller",
                    "practitioner_type": "Arzt",
                    "bill_date": "2024-03-15",
                    "bill_number": "2024-001234",
                    "total_amount": 29.49,
                    "currency": "EUR",
                }
            ]
        }
    }


class ExtractionError(BaseModel):
    """Schema for extraction errors returned by LLM providers.

    When extraction fails or produces invalid data, providers should return
    this error schema to provide debugging information.
    """

    error_type: str = Field(
        description="Type of error",
        examples=["parsing_error", "validation_error", "api_error"],
    )

    message: str = Field(
        description="Human-readable error message",
    )

    details: Optional[str] = Field(
        None,
        description="Additional error details for debugging",
    )
