"""Tests for bill processor."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from medical_bill_analyzer.core.bill_processor import BillProcessor, ProcessingResult
from medical_bill_analyzer.database.models import Bill, BillCreate
from medical_bill_analyzer.extraction.result import ExtractionResult, ExtractionStatus

# Valid SHA256 hash for testing (64 characters)
TEST_HASH = "a" * 64


@pytest.fixture
def mock_extractor():
    """Create mock BillExtractor."""
    extractor = Mock()
    return extractor


@pytest.fixture
def mock_repository():
    """Create mock BillRepository."""
    repository = Mock()
    return repository


@pytest.fixture
def processor(mock_extractor, mock_repository):
    """Create BillProcessor with mocks."""
    return BillProcessor(mock_extractor, mock_repository)


@pytest.fixture
def success_extraction():
    """Create successful extraction result."""
    return ExtractionResult(
        status=ExtractionStatus.SUCCESS,
        pdf_path=Path("test.pdf"),
        pdf_hash=TEST_HASH,
        extracted_data={
            "practitioner_name": "Dr. Smith",
            "practitioner_type": "Arzt",
            "bill_date": date(2024, 1, 1),
            "bill_number": "B-123",
            "total_amount": 50.0,
            "currency": "EUR",
        },
    )


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_create_empty_result(self):
        """Test creating empty result."""
        result = ProcessingResult()
        assert result.total_processed == 0
        assert result.total_skipped == 0
        assert result.total_failed == 0
        assert result.successful == []
        assert result.skipped == []
        assert result.failed == []

    def test_total_bills_property(self):
        """Test total_bills calculated property."""
        result = ProcessingResult(
            total_processed=5,
            total_skipped=2,
            total_failed=1,
        )
        assert result.total_bills == 8

    def test_success_rate_property(self):
        """Test success_rate calculated property."""
        result = ProcessingResult(
            total_processed=7,
            total_skipped=2,
            total_failed=1,
        )
        assert result.success_rate == 70.0

    def test_success_rate_zero_bills(self):
        """Test success_rate with zero bills."""
        result = ProcessingResult()
        assert result.success_rate == 0.0


class TestBillProcessorInit:
    """Test BillProcessor initialization."""

    def test_initialization(self, mock_extractor, mock_repository):
        """Test processor initializes correctly."""
        processor = BillProcessor(mock_extractor, mock_repository)
        assert processor.extractor == mock_extractor
        assert processor.repository == mock_repository
        assert processor.storage_path is None

    def test_initialization_with_storage(self, mock_extractor, mock_repository):
        """Test processor with storage path."""
        storage_path = Path("/storage")
        processor = BillProcessor(mock_extractor, mock_repository, storage_path)
        assert processor.storage_path == storage_path


class TestProcessSingleBill:
    """Test process_single_bill method."""

    def test_successful_processing(
        self, processor, mock_extractor, mock_repository, success_extraction
    ):
        """Test successful bill processing."""
        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = None  # No duplicate
        mock_repository.create.return_value = Bill(
            id=1,
            filename="test.pdf",
            file_hash=TEST_HASH,
            pdf_path=str(pdf_path),
            practitioner_name="Dr. Smith",
            total_amount=Decimal("50.00"),
            processed_at=datetime(2024, 1, 1),
        )

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 1
        assert result.total_skipped == 0
        assert result.total_failed == 0
        assert result.successful == [1]
        assert len(result.extraction_results) == 1
        mock_extractor.extract_from_pdf.assert_called_once_with(pdf_path)
        mock_repository.get_by_file_hash.assert_called_once_with(TEST_HASH)
        mock_repository.create.assert_called_once()

    def test_extraction_fails(self, processor, mock_extractor):
        """Test when extraction raises exception."""
        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.side_effect = Exception("Extraction error")

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 0
        assert result.total_skipped == 0
        assert result.total_failed == 1
        assert len(result.failed) == 1
        assert "test.pdf" in result.failed[0][0]
        assert "Extraction error" in result.failed[0][1]

    def test_extraction_not_successful(self, processor, mock_extractor):
        """Test when extraction status is not SUCCESS."""
        pdf_path = Path("test.pdf")
        extraction = ExtractionResult(
            status=ExtractionStatus.PDF_INVALID,
            pdf_path=pdf_path,
            pdf_hash="abc123",
            errors=["Corrupted PDF"],
        )
        mock_extractor.extract_from_pdf.return_value = extraction

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 0
        assert result.total_skipped == 1
        assert result.total_failed == 0
        assert len(result.skipped) == 1
        assert "pdf_invalid" in result.skipped[0][1].lower()

    def test_duplicate_detected(
        self, processor, mock_extractor, mock_repository, success_extraction
    ):
        """Test duplicate bill detection."""
        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = Bill(
            id=99,
            filename="other.pdf",
            file_hash=TEST_HASH,
            pdf_path="other.pdf",
            practitioner_name="Dr. Smith",
            total_amount=Decimal("50.00"),
            processed_at=datetime(2024, 1, 1),
        )

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 0
        assert result.total_skipped == 1
        assert result.total_failed == 0
        assert len(result.skipped) == 1
        assert "Duplicate" in result.skipped[0][1]
        assert "99" in result.skipped[0][1]
        mock_repository.create.assert_not_called()

    def test_duplicate_check_fails(
        self, processor, mock_extractor, mock_repository, success_extraction
    ):
        """Test when duplicate check raises exception."""
        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.side_effect = Exception("DB error")

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 0
        assert result.total_skipped == 0
        assert result.total_failed == 1
        assert "Duplicate check failed" in result.failed[0][1]

    def test_database_save_fails(
        self, processor, mock_extractor, mock_repository, success_extraction
    ):
        """Test when database save fails."""
        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = None
        mock_repository.create.side_effect = Exception("DB error")

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 0
        assert result.total_skipped == 0
        assert result.total_failed == 1
        assert "Database error" in result.failed[0][1]

    def test_with_notes(
        self, processor, mock_extractor, mock_repository, success_extraction
    ):
        """Test processing with notes."""
        pdf_path = Path("test.pdf")
        notes = "Emergency visit"
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = None
        mock_repository.create.return_value = Bill(
            id=1,
            filename="test.pdf",
            file_hash=TEST_HASH,
            pdf_path=str(pdf_path),
            notes=notes,
            processed_at=datetime(2024, 1, 1),
        )

        result = processor.process_single_bill(pdf_path, notes=notes)

        assert result.total_processed == 1
        # Verify notes were passed to create
        create_call = mock_repository.create.call_args[0][0]
        assert isinstance(create_call, BillCreate)
        assert create_call.notes == notes

    @patch("medical_bill_analyzer.core.bill_processor.shutil.copy2")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_with_storage_path(
        self,
        mock_exists,
        mock_mkdir,
        mock_copy,
        mock_extractor,
        mock_repository,
        success_extraction,
    ):
        """Test PDF copied to storage when storage_path is set."""
        storage_path = Path("/tmp/storage")
        processor = BillProcessor(mock_extractor, mock_repository, storage_path)

        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = None
        mock_repository.create.return_value = Bill(
            id=1,
            filename="test.pdf",
            file_hash=TEST_HASH,
            pdf_path="test.pdf",
            processed_at=datetime(2024, 1, 1),
        )
        mock_exists.return_value = False  # Destination doesn't exist yet

        result = processor.process_single_bill(pdf_path)

        assert result.total_processed == 1
        # Storage operations called
        mock_mkdir.assert_called()
        mock_copy.assert_called_once()

    @patch("medical_bill_analyzer.core.bill_processor.shutil.copy2")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    def test_storage_copy_failure_doesnt_fail_processing(
        self,
        mock_exists,
        mock_mkdir,
        mock_copy,
        mock_extractor,
        mock_repository,
        success_extraction,
    ):
        """Test that storage copy failure doesn't fail the whole operation."""
        storage_path = Path("/tmp/storage")
        processor = BillProcessor(mock_extractor, mock_repository, storage_path)

        pdf_path = Path("test.pdf")
        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = None
        mock_repository.create.return_value = Bill(
            id=1,
            filename="test.pdf",
            file_hash=TEST_HASH,
            pdf_path="test.pdf",
            processed_at=datetime(2024, 1, 1),
        )
        mock_exists.return_value = False  # Destination doesn't exist yet
        mock_copy.side_effect = Exception("Copy failed")

        result = processor.process_single_bill(pdf_path)

        # Processing still succeeds despite storage failure
        assert result.total_processed == 1


class TestProcessMultipleBills:
    """Test process_multiple_bills method."""

    def test_process_multiple_success(
        self, processor, mock_extractor, mock_repository
    ):
        """Test processing multiple bills successfully."""
        pdfs = [Path("bill1.pdf"), Path("bill2.pdf"), Path("bill3.pdf")]

        # Mock successful extractions
        mock_extractor.extract_from_pdf.side_effect = [
            ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                pdf_path=pdf,
                pdf_hash="b" * 64,  # Valid 64-char hash
                extracted_data={"practitioner_name": f"Dr. {i}", "total_amount": 50.0},
            )
            for i, pdf in enumerate(pdfs)
        ]
        mock_repository.get_by_file_hash.return_value = None
        mock_repository.create.side_effect = [
            Bill(
                id=i,
                filename=f"bill{i}.pdf",
                file_hash="b" * 64,  # Valid 64-char hash
                pdf_path=f"bill{i}.pdf",
                processed_at=datetime(2024, 1, 1),
            )
            for i in range(1, 4)
        ]

        result = processor.process_multiple_bills(pdfs)

        assert result.total_processed == 3
        assert result.total_skipped == 0
        assert result.total_failed == 0
        assert result.successful == [1, 2, 3]
        assert result.total_bills == 3
        assert result.success_rate == 100.0

    def test_process_multiple_mixed_results(
        self, processor, mock_extractor, mock_repository
    ):
        """Test processing with mixed success/skip/failure."""
        pdfs = [Path("bill1.pdf"), Path("bill2.pdf"), Path("bill3.pdf")]

        # First: success, Second: invalid PDF, Third: duplicate
        mock_extractor.extract_from_pdf.side_effect = [
            ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                pdf_path=pdfs[0],
                pdf_hash="c" * 64,  # Valid 64-char hash
                extracted_data={"practitioner_name": "Dr. 1", "total_amount": 50.0},
            ),
            ExtractionResult(
                status=ExtractionStatus.PDF_INVALID,
                pdf_path=pdfs[1],
                pdf_hash="d" * 64,  # Valid 64-char hash
                errors=["Corrupted"],
            ),
            ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                pdf_path=pdfs[2],
                pdf_hash="e" * 64,  # Valid 64-char hash
                extracted_data={"practitioner_name": "Dr. 3", "total_amount": 50.0},
            ),
        ]
        # First and third: no duplicate, but make third fail at DB save
        mock_repository.get_by_file_hash.side_effect = [
            None,  # First bill - no duplicate
            None,  # Third bill - no duplicate
        ]
        mock_repository.create.side_effect = [
            Bill(
                id=1,
                filename="bill1.pdf",
                file_hash="c" * 64,  # Valid 64-char hash
                pdf_path="bill1.pdf",
                processed_at=datetime(2024, 1, 1),
            ),  # First succeeds
            Exception("DB error"),  # Third fails
        ]

        result = processor.process_multiple_bills(pdfs)

        assert result.total_processed == 1
        assert result.total_skipped == 1  # Second (invalid PDF)
        assert result.total_failed == 1  # Third (DB error)
        assert result.total_bills == 3
        assert result.success_rate == pytest.approx(33.33, rel=0.01)

    def test_process_empty_list(self, processor):
        """Test processing empty list."""
        result = processor.process_multiple_bills([])

        assert result.total_processed == 0
        assert result.total_bills == 0
        assert result.success_rate == 0.0

    def test_notes_applied_to_all(
        self, processor, mock_extractor, mock_repository, success_extraction
    ):
        """Test notes are applied to all bills."""
        pdfs = [Path("bill1.pdf"), Path("bill2.pdf")]
        notes = "Batch import"

        mock_extractor.extract_from_pdf.return_value = success_extraction
        mock_repository.get_by_file_hash.return_value = None
        mock_repository.create.side_effect = [
            Bill(
                id=1,
                filename="bill1.pdf",
                file_hash=TEST_HASH,
                pdf_path="bill1.pdf",
                processed_at=datetime(2024, 1, 1),
            ),
            Bill(
                id=2,
                filename="bill2.pdf",
                file_hash=TEST_HASH,
                pdf_path="bill2.pdf",
                processed_at=datetime(2024, 1, 1),
            ),
        ]

        result = processor.process_multiple_bills(pdfs, notes=notes)

        assert result.total_processed == 2
        # Check notes were passed in both create calls
        for call in mock_repository.create.call_args_list:
            bill_create = call[0][0]
            assert bill_create.notes == notes
