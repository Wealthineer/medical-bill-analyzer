"""Add Bills Wizard screen for Medical Bill Analyzer TUI."""

from pathlib import Path
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

from medical_bill_analyzer.cli.utils import (
    get_credential_repository,
    get_database_path,
    load_config,
)
from medical_bill_analyzer.core.bill_processor import BillProcessor, ProcessingResult
from medical_bill_analyzer.database.repositories import BillRepository
from medical_bill_analyzer.extraction.extractor import BillExtractor
from medical_bill_analyzer.llm.factory import create_llm_provider


class AddWizardScreen(Screen):
    """Multi-step wizard for adding PDF bills.

    Steps:
    1. File Selection: Enter path to PDF or directory
    2. Processing: Extract and save bills with progress
    3. Results: Show summary of successful/skipped/failed

    Calls the same BillProcessor as CLI add command (no duplication).
    """

    CSS = """
    AddWizardScreen {
        background: $surface;
    }

    #wizard-container {
        height: 100%;
        padding: 1 2;
    }

    #step-title {
        text-style: bold;
        color: $accent;
        padding: 1 0;
    }

    #step-content {
        padding: 1 0;
        height: auto;
    }

    #file-input {
        width: 100%;
        margin: 1 0;
    }

    #button-container {
        height: auto;
        padding: 1 0;
    }

    Button {
        margin: 0 1;
    }

    #status {
        padding: 1 0;
        min-height: 5;
        height: auto;
        overflow-y: auto;
    }

    #help-text {
        padding: 1 0;
        color: $text-muted;
    }

    .hidden {
        display: none;
    }
    """

    def __init__(self):
        """Initialize add wizard."""
        super().__init__()
        self.current_step = 1
        self.selected_files: List[Path] = []
        self.processing_result: Optional[ProcessingResult] = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Static("Step 1: Select PDF Files", id="step-title"),
            Container(
                Label("Enter path to PDF file or directory:"),
                Input(
                    placeholder="/path/to/bill.pdf or /path/to/bills/",
                    id="file-input",
                ),
                id="step-content",
            ),
            Container(
                Button("Next", id="next-btn", variant="primary"),
                Button("Delete These Bills", id="delete-btn", variant="error", classes="hidden"),
                Button("Cancel", id="cancel-btn", variant="default"),
                id="button-container",
            ),
            Static(id="status"),
            Static(
                "Tip: You can drag & drop PDF files or enter the path manually",
                id="help-text",
            ),
            id="wizard-container",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "cancel-btn":
            self.app.pop_screen()
        elif event.button.id == "delete-btn":
            self._delete_added_bills()
        elif event.button.id == "next-btn":
            if self.current_step == 1:
                self._validate_and_process_files()
            elif self.current_step == 2:
                # After viewing results, go back to dashboard
                self.app.pop_screen()

    def _validate_and_process_files(self) -> None:
        """Validate file input and start processing."""
        # Get file path from input
        file_input = self.query_one("#file-input", Input)
        path_str = file_input.value.strip()

        if not path_str:
            self.app.notify("Please enter a path", severity="warning", timeout=3)
            return

        # Clean up path (remove quotes from drag-and-drop, extra whitespace)
        path_str = path_str.strip().strip("'\"")

        # Handle backslash-escaped spaces from drag-and-drop (e.g., "My\ Documents")
        # Replace "\ " with " " to handle escaped spaces
        path_str = path_str.replace("\\ ", " ")

        # Validate path - try absolute first, then relative to cwd
        path = Path(path_str).expanduser().resolve()

        # Show debug info in status
        status = self.query_one("#status", Static)
        status.update(f"Looking for: {path}\n(Resolved from: {path_str})")

        if not path.exists():
            self.app.notify(
                f"Path not found: {path}",
                severity="error",
                timeout=5,
            )
            status.update(
                f"❌ Path not found!\n\n"
                f"You entered: {path_str}\n"
                f"Resolved to: {path}\n\n"
                f"Please check:\n"
                f"  • File/directory exists\n"
                f"  • Path is spelled correctly\n"
                f"  • You have permission to access it"
            )
            return

        # Collect PDF files
        if path.is_file():
            if path.suffix.lower() != ".pdf":
                self.app.notify(
                    "File must be a PDF",
                    severity="error",
                    timeout=5,
                )
                return
            self.selected_files = [path]
        elif path.is_dir():
            # Find all PDFs in directory
            pdf_files = list(path.glob("*.pdf"))
            if not pdf_files:
                self.app.notify(
                    "No PDF files found in directory",
                    severity="warning",
                    timeout=5,
                )
                return
            self.selected_files = pdf_files
        else:
            self.app.notify(
                "Invalid path",
                severity="error",
                timeout=5,
            )
            return

        # Start processing
        self._process_files()

    def _process_files(self) -> None:
        """Process PDFs using BillProcessor (REUSE from CLI)."""
        # Update UI to show processing
        self.query_one("#step-title", Static).update("Step 2: Processing Bills")
        self.query_one("#next-btn", Button).disabled = True

        status = self.query_one("#status", Static)
        status.update(f"Processing {len(self.selected_files)} file(s)...\nThis may take a moment.")

        try:
            # Setup (SAME AS CLI add command)
            settings = load_config()
            db_path = get_database_path(settings)
            credential_repo = get_credential_repository(settings)

            # Create LLM provider
            llm_config = settings.llm.get_provider_config(credential_repo)
            llm_provider = create_llm_provider(
                provider_name=settings.llm.provider,
                config=llm_config,
            )

            # Create extractor and processor
            extractor = BillExtractor(llm_provider)
            repository = BillRepository(db_path)
            processor = BillProcessor(
                extractor=extractor,
                repository=repository,
                storage_path=settings.storage.pdf_storage_path,
            )

            # Process files (SAME LOGIC AS CLI)
            self.processing_result = processor.process_multiple_bills(
                pdf_paths=self.selected_files,
                notes="Added via TUI",
            )

            # Show results
            self._show_results()

        except Exception as e:
            status.update(f"Error: {e}")
            self.app.notify(
                f"Processing failed: {e}",
                severity="error",
                timeout=5,
            )
            self.query_one("#next-btn", Button).disabled = False
            self.query_one("#next-btn", Button).label = "Retry"

    def _show_results(self) -> None:
        """Show processing results with extracted bill details."""
        if not self.processing_result:
            return

        result = self.processing_result

        # Update UI
        self.query_one("#step-title", Static).update("Step 3: Results")
        self.query_one("#next-btn", Button).disabled = False
        self.query_one("#next-btn", Button).label = "Done"

        # Show delete button only if bills were successfully added
        delete_btn = self.query_one("#delete-btn", Button)
        if result.total_processed > 0:
            delete_btn.remove_class("hidden")
            # Update help text to explain delete option
            self.query_one("#help-text", Static).update(
                "Review the extracted data above. If incorrect, click 'Delete These Bills' to remove them."
            )
        else:
            delete_btn.add_class("hidden")

        # Build results text
        results_text = f"""
✓ Successfully processed: {result.total_processed}
⚠ Skipped (duplicates):   {result.total_skipped}
✗ Failed:                 {result.total_failed}

Success rate: {result.success_rate:.1f}%
"""

        # Add details about successfully processed bills
        if result.extraction_results:
            successful_extractions = [
                r for r in result.extraction_results if r.is_success
            ]

            if successful_extractions:
                results_text += "\n" + "=" * 60 + "\n"
                results_text += "Successfully Added Bills:\n"
                results_text += "=" * 60 + "\n\n"

                for extraction in successful_extractions:
                    # Format the bill details
                    bill_date_str = extraction.bill_date.strftime("%d.%m.%Y") if extraction.bill_date else "Unknown"
                    amount_str = f"€{extraction.total_amount:.2f}" if extraction.total_amount else "Unknown"

                    results_text += f"📄 {extraction.pdf_path.name}\n"
                    results_text += f"   Practitioner: {extraction.practitioner_name or 'Unknown'}\n"
                    results_text += f"   Type:         {extraction.practitioner_type or 'Unknown'}\n"
                    results_text += f"   Date:         {bill_date_str}\n"
                    results_text += f"   Amount:       {amount_str}\n"
                    results_text += f"   Bill #:       {extraction.bill_number or 'N/A'}\n"

                    # Show warnings if any
                    if extraction.warnings:
                        results_text += f"   ⚠ Warnings:   {', '.join(extraction.warnings)}\n"

                    results_text += "\n"

        # Add details about failed bills
        if result.failed:
            results_text += "\n" + "=" * 60 + "\n"
            results_text += "Failed Files:\n"
            results_text += "=" * 60 + "\n"
            for path, error in result.failed:
                results_text += f"  ✗ {path.name}: {error}\n"

        # Add details about skipped bills
        if result.skipped:
            results_text += "\n" + "=" * 60 + "\n"
            results_text += "Skipped Files:\n"
            results_text += "=" * 60 + "\n"
            for path, reason in result.skipped:
                results_text += f"  ⚠ {path.name}: {reason}\n"

        status = self.query_one("#status", Static)
        status.update(results_text)

        # Show notification
        if result.total_processed > 0:
            self.app.notify(
                f"Successfully processed {result.total_processed} bill(s)",
                severity="information",
                timeout=5,
            )

    def _delete_added_bills(self) -> None:
        """Delete all bills that were just added."""
        if not self.processing_result or not self.processing_result.successful:
            self.app.notify("No bills to delete", severity="warning", timeout=3)
            return

        result = self.processing_result
        bill_ids = result.successful

        try:
            # Delete all successful bills
            settings = load_config()
            db_path = get_database_path(settings)
            repository = BillRepository(db_path)

            deleted_count = 0
            for bill_id in bill_ids:
                if repository.delete(bill_id):
                    deleted_count += 1

            # Update UI
            if deleted_count > 0:
                self.app.notify(
                    f"Deleted {deleted_count} bill(s)",
                    severity="information",
                    timeout=3,
                )

                # Clear the result and reset to step 1
                self.processing_result = None
                self.selected_files = []
                self.current_step = 1

                # Reset UI
                self.query_one("#step-title", Static).update("Step 1: Select PDF Files")
                self.query_one("#file-input", Input).value = ""
                self.query_one("#status", Static).update("")
                self.query_one("#next-btn", Button).label = "Next"
                self.query_one("#next-btn", Button).disabled = False
                self.query_one("#delete-btn", Button).add_class("hidden")
                self.query_one("#help-text", Static).update(
                    "Tip: You can drag & drop PDF files or enter the path manually"
                )
            else:
                self.app.notify(
                    "No bills were deleted",
                    severity="warning",
                    timeout=3,
                )

        except Exception as e:
            self.app.notify(
                f"Error deleting bills: {e}",
                severity="error",
                timeout=5,
            )
