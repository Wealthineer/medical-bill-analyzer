"""Dashboard screen for Medical Bill Analyzer TUI."""

from datetime import date
from decimal import Decimal

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from medical_bill_analyzer.cli.utils import format_currency, get_database_path, load_config
from medical_bill_analyzer.core.bonus_calculator import BonusCalculator
from medical_bill_analyzer.database.models import BillFilter
from medical_bill_analyzer.database.repositories import BillRepository


class DashboardScreen(Screen):
    """Main dashboard screen showing current year summary and recent bills.

    Displays:
    - Total bills for current year
    - Total costs for current year
    - Bonus threshold status (over/under)
    - Recent bills table (last 10)

    Calls the same core modules as CLI commands (no business logic duplication).
    """

    CSS = """
    DashboardScreen {
        background: $surface;
    }

    #summary-container {
        height: auto;
        padding: 1 2;
        border: solid $accent;
        margin: 1 2;
    }

    #summary-title {
        text-style: bold;
        color: $accent;
        padding-bottom: 1;
    }

    #summary-stats {
        padding: 0 1;
    }

    #recent-container {
        height: auto;
        padding: 1 2;
        border: solid $primary;
        margin: 1 2;
    }

    #recent-title {
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }

    #recent-bills {
        height: 15;
    }

    #help-text {
        text-align: center;
        padding: 1;
        color: $text-muted;
    }

    .status-ok {
        color: $success;
    }

    .status-warning {
        color: $warning;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        current_year = date.today().year
        yield Header()
        yield Container(
            Static(f"📊 {current_year} Summary", id="summary-title", classes="title"),
            Static(id="summary-stats"),
            id="summary-container",
        )
        yield Container(
            Static("📁 Recent Bills", id="recent-title", classes="title"),
            DataTable(id="recent-bills"),
            id="recent-container",
        )
        yield Static(
            "Press S for Stats | B for Bills | A to Add | Q to Quit",
            id="help-text",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load dashboard data when screen is displayed."""
        self._load_dashboard_data()

    def _load_dashboard_data(self) -> None:
        """Load current year summary and recent bills from database.

        Calls:
        - load_config() - Same as CLI
        - BillRepository - Same as CLI
        - BonusCalculator - Same as CLI
        """
        try:
            # Load config and repository (REUSE from CLI)
            settings = load_config()
            db_path = get_database_path(settings)
            repository = BillRepository(db_path)

            # Calculate 2024 summary
            current_year = date.today().year
            calculator = BonusCalculator(repository)
            total_2024 = calculator.calculate_total(year=current_year)

            # Get bonus recommendation
            threshold = Decimal(str(settings.bonus.default_threshold))
            recommendation = calculator.get_recommendation_for_year(
                year=current_year,
                threshold=threshold,
            )

            # Get bill count
            bills_2024 = repository.filter(BillFilter(year=current_year))
            bill_count = len(bills_2024)

            # Calculate average
            avg_amount = total_2024 / bill_count if bill_count > 0 else Decimal("0")

            # Update summary widget
            summary_widget = self.query_one("#summary-stats", Static)

            # Determine status styling
            if recommendation.should_keep_bonus:
                status_text = "✅ UNDER THRESHOLD"
                status_class = "status-ok"
            else:
                status_text = "⚠️  OVER THRESHOLD"
                status_class = "status-warning"

            summary_text = f"""
Total Bills:     {bill_count}
Total Costs:     {format_currency(float(total_2024))}
Average per Bill: {format_currency(float(avg_amount))}
Bonus Threshold:  {format_currency(float(threshold))}
Status:          {status_text}
            """.strip()

            summary_widget.update(summary_text)

            # Color the status line
            if not recommendation.should_keep_bonus:
                summary_widget.add_class(status_class)

            # Load recent bills table
            self._load_recent_bills(repository)

        except Exception as e:
            # Show error in summary widget
            summary_widget = self.query_one("#summary-stats", Static)
            summary_widget.update(f"Error loading data: {e}")
            self.app.notify(
                f"Failed to load dashboard: {e}",
                severity="error",
                timeout=5,
            )

    def _load_recent_bills(self, repository: BillRepository) -> None:
        """Load and display recent bills table.

        Args:
            repository: BillRepository instance
        """
        try:
            # Get all bills and sort by date
            all_bills = repository.get_all()
            recent_bills = sorted(all_bills, key=lambda b: b.bill_date, reverse=True)[:10]

            # Populate table
            table = self.query_one("#recent-bills", DataTable)
            table.add_columns("Date", "Practitioner", "Amount", "Type")

            if not recent_bills:
                # No bills yet
                table.add_row(
                    "No bills yet",
                    "Use [A] to add bills",
                    "-",
                    "-",
                )
            else:
                for bill in recent_bills:
                    table.add_row(
                        bill.bill_date.strftime("%d.%m.%Y"),
                        bill.practitioner_name or "Unknown",
                        format_currency(float(bill.total_amount)),
                        bill.practitioner_type or "-",
                    )

        except Exception as e:
            self.app.notify(
                f"Failed to load recent bills: {e}",
                severity="error",
                timeout=5,
            )
