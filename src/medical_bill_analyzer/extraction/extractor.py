"""Bill information extractor - orchestrates PDF and LLM processing."""

from pathlib import Path
from typing import Optional

from ..core.exceptions import (
    LLMExtractionError,
    PDFProcessingError,
    ValidationError,
)
from ..llm.base import LLMProvider
from ..llm.schemas import BasicExtractionResponse
from ..pdf.extractor import extract_text_from_pdf
from ..pdf.utils import get_pdf_hash
from ..pdf.validator import validate_pdf
from ..utils.logger import get_logger
from .result import ExtractionResult, ExtractionStatus

logger = get_logger(__name__)


class BillExtractor:
    """Orchestrates bill information extraction from PDFs.

    This class ties together PDF processing (validation, text extraction) with
    LLM-based information extraction to provide a complete extraction pipeline.

    Example:
        >>> from medical_bill_analyzer.llm.factory import create_llm_provider
        >>> config = {"model": "claude-sonnet-4-20250514", "api_key": "..."}
        >>> provider = create_llm_provider("anthropic", config)
        >>> extractor = BillExtractor(provider)
        >>> result = extractor.extract_from_pdf(Path("bill.pdf"))
        >>> if result.is_success:
        ...     print(f"Amount: €{result.total_amount}")
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize bill extractor.

        Args:
            llm_provider: LLM provider instance for information extraction
        """
        self.llm_provider = llm_provider
        logger.info(f"Initialized BillExtractor with {type(llm_provider).__name__}")

    def extract_from_pdf(
        self, pdf_path: Path, extraction_type: str = "basic"
    ) -> ExtractionResult:
        """Extract bill information from PDF.

        This is the main entry point for extraction. It orchestrates:
        1. PDF validation
        2. Text extraction
        3. LLM-based information extraction
        4. Response validation

        Args:
            pdf_path: Path to PDF file
            extraction_type: Type of extraction ("basic" or "line_items")

        Returns:
            ExtractionResult with extraction outcome and data

        Example:
            >>> result = extractor.extract_from_pdf(Path("bill.pdf"))
            >>> print(result.status)
            ExtractionStatus.SUCCESS
        """
        logger.info(f"Starting extraction from {pdf_path}")

        # Step 1: Calculate PDF hash (before validation for error cases)
        try:
            pdf_hash = get_pdf_hash(pdf_path)
        except Exception as e:
            logger.error(f"Failed to calculate PDF hash: {e}")
            return ExtractionResult(
                status=ExtractionStatus.PDF_INVALID,
                pdf_path=pdf_path,
                pdf_hash="",
                errors=[f"Failed to access PDF file: {str(e)}"],
            )

        # Step 2: Validate PDF
        try:
            validation_result = validate_pdf(pdf_path)
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return ExtractionResult(
                status=ExtractionStatus.PDF_INVALID,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                errors=[f"PDF validation failed: {str(e)}"],
            )

        if not validation_result.is_processable:
            logger.warning(f"PDF not processable: {validation_result.errors}")
            status = (
                ExtractionStatus.PDF_NOT_PROCESSABLE
                if validation_result.is_scanned
                else ExtractionStatus.PDF_INVALID
            )
            return ExtractionResult(
                status=status,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                errors=validation_result.errors,
                warnings=validation_result.warnings,
            )

        # Step 3: Extract text from PDF
        try:
            text = extract_text_from_pdf(pdf_path)
            logger.info(f"Extracted {len(text)} characters from PDF")
        except PDFProcessingError as e:
            logger.error(f"Text extraction failed: {e}")
            return ExtractionResult(
                status=ExtractionStatus.PDF_INVALID,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                errors=[str(e)],
            )
        except Exception as e:
            logger.error(f"Unexpected error during text extraction: {e}")
            return ExtractionResult(
                status=ExtractionStatus.PDF_INVALID,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                errors=[f"Text extraction failed: {str(e)}"],
            )

        # Step 4: Extract information with LLM
        try:
            logger.info(f"Sending to LLM for {extraction_type} extraction...")
            extracted_dict = self.llm_provider.extract(text, extraction_type)
            logger.info("LLM extraction successful")
        except LLMExtractionError as e:
            logger.error(f"LLM extraction failed: {e}")
            return ExtractionResult(
                status=ExtractionStatus.EXTRACTION_FAILED,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                errors=[str(e)],
            )
        except Exception as e:
            logger.error(f"Unexpected error during LLM extraction: {e}")
            return ExtractionResult(
                status=ExtractionStatus.EXTRACTION_FAILED,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                errors=[f"LLM extraction failed: {str(e)}"],
            )

        # Step 5: Validate extracted data with Pydantic
        try:
            validated_response = BasicExtractionResponse(**extracted_dict)
            logger.info("Data validation successful")

            # Convert to dict for storage (with date as string)
            validated_dict = validated_response.model_dump()
            if validated_dict.get("bill_date"):
                validated_dict["bill_date"] = validated_response.bill_date

            return ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                extracted_data=validated_dict,
                warnings=validation_result.warnings,  # Include PDF warnings
            )

        except ValidationError as e:
            logger.error(f"Data validation failed: {e}")
            return ExtractionResult(
                status=ExtractionStatus.VALIDATION_FAILED,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                extracted_data=extracted_dict,  # Include raw data for debugging
                errors=[f"Validation error: {str(e)}"],
            )
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            return ExtractionResult(
                status=ExtractionStatus.VALIDATION_FAILED,
                pdf_path=pdf_path,
                pdf_hash=pdf_hash,
                extracted_data=extracted_dict,
                errors=[f"Validation failed: {str(e)}"],
            )

    def extract_from_text(
        self, text: str, extraction_type: str = "basic"
    ) -> Optional[dict]:
        """Extract information from bill text (for testing/debugging).

        This method bypasses PDF processing and directly extracts information
        from provided text. Useful for testing the LLM extraction in isolation.

        Args:
            text: Bill text to extract from
            extraction_type: Type of extraction ("basic" or "line_items")

        Returns:
            Dictionary of extracted information, or None if extraction fails

        Raises:
            LLMExtractionError: If LLM extraction fails
            ValidationError: If extracted data fails validation

        Example:
            >>> text = "Rechnung Dr. med. Müller\\n29.49 EUR"
            >>> data = extractor.extract_from_text(text)
            >>> print(data['practitioner_name'])
            Dr. med. Müller
        """
        logger.info("Extracting from text (bypassing PDF processing)")

        # Extract with LLM
        extracted_dict = self.llm_provider.extract(text, extraction_type)

        # Validate with Pydantic
        validated_response = BasicExtractionResponse(**extracted_dict)

        # Return validated dict
        result_dict = validated_response.model_dump()
        if result_dict.get("bill_date"):
            result_dict["bill_date"] = validated_response.bill_date

        return result_dict
