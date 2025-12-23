"""Bills management screen for Medical Bill Analyzer TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Static

from medical_bill_analyzer.cli.utils import format_currency, get_database_path, load_config
from medical_bill_analyzer.database.repositories import BillRepository


class BillsScreen(Screen):
    """Bill management screen with search and list functionality.

    Displays:
    - Search input for filtering bills
    - DataTable with all bills sorted by date (newest first)
    - Summary with total count and amount

    Calls the same BillRepository as CLI commands (no duplication).
    """

    CSS = """
    BillsScreen {
        background: $surface;
    }

    #bills-container {
        height: 100%;
        padding: 1 2;
    }

    #search-container {
        height: auto;
        padding: 1 0;
    }

    #search-input {
        width: 100%;
    }

    #bills-table {
        height: auto;
        min-height: 25;
    }

    #summary {
        padding: 1;
        text-align: center;
        color: $text-muted;
    }

    #help-text {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("delete", "delete_selected", "Delete"),
        ("x", "delete_selected", "Delete"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Container(
                Input(
                    placeholder="Search practitioner or bill number...",
                    id="search-input",
                ),
                id="search-container",
            ),
            DataTable(id="bills-table"),
            Static(id="summary"),
            Static(
                "Use ↑↓ to select | [X] or [Del] to delete | [R]efresh | [Esc] to go back",
                id="help-text",
            ),
            id="bills-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load bills when screen is displayed."""
        # Setup table columns
        table = self.query_one("#bills-table", DataTable)
        table.cursor_type = "row"  # Enable row selection
        table.add_columns(
            "ID",
            "Date",
            "Practitioner",
            "Type",
            "Amount",
            "Status",
        )

        # Load bills
        self._load_bills()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self._load_bills(search_term=event.value)

    def action_refresh(self) -> None:
        """Refresh bills list."""
        self.app.notify("Refreshing bills...", timeout=2)
        search_input = self.query_one("#search-input", Input)
        self._load_bills(search_term=search_input.value or None)

    def action_delete_selected(self) -> None:
        """Delete the selected bill."""
        table = self.query_one("#bills-table", DataTable)

        # Get cursor position
        if table.cursor_row is None or table.cursor_row < 0:
            self.app.notify("No bill selected", severity="warning", timeout=3)
            return

        # Get the bill ID from the selected row
        try:
            row_key = table.get_row_at(table.cursor_row)
            bill_id_str = str(row_key[0])  # First column is ID

            # Check if it's a valid bill ID (not placeholder text)
            if not bill_id_str.isdigit():
                self.app.notify("No bills to delete", severity="warning", timeout=3)
                return

            bill_id = int(bill_id_str)

            # Delete the bill
            settings = load_config()
            db_path = get_database_path(settings)
            repository = BillRepository(db_path)

            deleted = repository.delete(bill_id)

            if deleted:
                self.app.notify(f"Bill #{bill_id} deleted", severity="information", timeout=3)
                # Refresh the list
                search_input = self.query_one("#search-input", Input)
                self._load_bills(search_term=search_input.value or None)
            else:
                self.app.notify(f"Failed to delete bill #{bill_id}", severity="error", timeout=3)

        except Exception as e:
            self.app.notify(f"Error deleting bill: {e}", severity="error", timeout=5)

    def _load_bills(self, search_term: str = None) -> None:
        """Load bills from database (REUSE BillRepository).

        Args:
            search_term: Optional search term to filter bills
        """
        try:
            # Load config and repository (SAME AS CLI)
            settings = load_config()
            db_path = get_database_path(settings)
            repository = BillRepository(db_path)

            # Get all bills
            bills = repository.get_all()

            # Filter by search term if provided
            if search_term:
                search_lower = search_term.lower()
                bills = [
                    b
                    for b in bills
                    if search_lower in (b.practitioner_name or "").lower()
                    or search_lower in (b.bill_number or "").lower()
                ]

            # Sort by date (newest first)
            bills = sorted(bills, key=lambda b: b.bill_date, reverse=True)

            # Clear and populate table
            table = self.query_one("#bills-table", DataTable)
            table.clear()

            if not bills:
                # No bills match
                if search_term:
                    table.add_row(
                        "No matches",
                        "Try a different search",
                        "-",
                        "-",
                        "-",
                        "-",
                    )
                else:
                    table.add_row(
                        "No bills yet",
                        "Use [A] to add bills",
                        "-",
                        "-",
                        "-",
                        "-",
                    )
            else:
                for bill in bills:
                    # Status indicator
                    if bill.extraction_status == "success":
                        status = "✓"
                    elif bill.extraction_status == "needs_review":
                        status = "⚠"
                    else:
                        status = "✗"

                    table.add_row(
                        str(bill.id),
                        bill.bill_date.strftime("%d.%m.%Y"),
                        bill.practitioner_name or "Unknown",
                        bill.practitioner_type or "-",
                        format_currency(float(bill.total_amount)),
                        status,
                    )

            # Update summary
            total_amount = sum(b.total_amount for b in bills)
            summary = self.query_one("#summary", Static)
            summary.update(
                f"Showing {len(bills)} bill(s) | Total: {format_currency(float(total_amount))}"
            )

        except Exception as e:
            self.app.notify(
                f"Failed to load bills: {e}",
                severity="error",
                timeout=5,
            )
