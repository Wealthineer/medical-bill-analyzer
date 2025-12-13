"""Pydantic models for database entities."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class BillBase(BaseModel):
    """Base bill model with common fields."""

    filename: str = Field(..., min_length=1, description="PDF filename")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 file hash")
    pdf_path: str = Field(..., description="Path to stored PDF file")

    practitioner_name: Optional[str] = Field(None, description="Name of doctor or clinic")
    practitioner_type: Optional[str] = Field(
        None,
        description="Type of practitioner (Arzt, Zahnarzt, etc.)"
    )

    bill_date: Optional[date] = Field(None, description="Date of bill")
    bill_number: Optional[str] = Field(None, description="Bill/invoice number")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount in EUR")
    currency: str = Field(default="EUR", description="Currency code")

    extraction_status: Literal["success", "failed", "needs_review"] = Field(
        default="success",
        description="Status of information extraction"
    )
    raw_extraction_json: Optional[str] = Field(
        None,
        description="Raw JSON response from LLM extraction"
    )
    notes: Optional[str] = Field(None, description="User notes")

    @field_validator("practitioner_type")
    @classmethod
    def validate_practitioner_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate practitioner type against allowed values."""
        if v is None:
            return v

        valid_types = {
            "Arzt",
            "Zahnarzt",
            "Heilpraktiker",
            "Krankenhaus",
            "Labor",
            "Apotheke",
            "Sonstige",
        }

        if v not in valid_types:
            raise ValueError(
                f"Invalid practitioner type '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

        return v


class BillCreate(BillBase):
    """Model for creating a new bill."""

    pass


class BillUpdate(BaseModel):
    """Model for updating an existing bill (all fields optional)."""

    practitioner_name: Optional[str] = None
    practitioner_type: Optional[str] = None
    bill_date: Optional[date] = None
    bill_number: Optional[str] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    extraction_status: Optional[Literal["success", "failed", "needs_review"]] = None
    raw_extraction_json: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("practitioner_type")
    @classmethod
    def validate_practitioner_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate practitioner type against allowed values."""
        if v is None:
            return v

        valid_types = {
            "Arzt",
            "Zahnarzt",
            "Heilpraktiker",
            "Krankenhaus",
            "Labor",
            "Apotheke",
            "Sonstige",
        }

        if v not in valid_types:
            raise ValueError(
                f"Invalid practitioner type '{v}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )

        return v


class Bill(BillBase):
    """Complete bill model with database fields."""

    id: int = Field(..., description="Database ID")
    processed_at: datetime = Field(..., description="Timestamp when bill was processed")

    class Config:
        from_attributes = True  # Allow creation from ORM objects


class BillFilter(BaseModel):
    """Filter criteria for querying bills."""

    year: Optional[int] = Field(None, ge=1900, le=2100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    practitioner_name: Optional[str] = None
    practitioner_type: Optional[str] = None
    extraction_status: Optional[Literal["success", "failed", "needs_review"]] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Validate that end_date is after start_date."""
        if v is not None and info.data.get("start_date") is not None:
            if v < info.data["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v
