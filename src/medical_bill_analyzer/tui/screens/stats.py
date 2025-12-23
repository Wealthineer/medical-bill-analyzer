"""Statistics screen for Medical Bill Analyzer TUI."""

from datetime import date

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from medical_bill_analyzer.analytics import AnalyticsEngine
from medical_bill_analyzer.cli.utils import format_currency, get_database_path, load_config
from medical_bill_analyzer.database.models import BillFilter
from medical_bill_analyzer.database.repositories import BillRepository


class StatsScreen(Screen):
    """Statistics screen with tabs for different analytics views.

    Displays:
    - Practitioner tab: Top practitioners by spending
    - Category tab: Spending breakdown by practitioner type
    - Monthly tab: Monthly spending trends

    Calls the same AnalyticsEngine as CLI stats command (no duplication).
    """

    CSS = """
    StatsScreen {
        background: $surface;
    }

    #stats-container {
        height: 100%;
        padding: 1 2;
    }

    #filter-bar {
        height: auto;
        padding: 1 0;
    }

    DataTable {
        height: auto;
        min-height: 20;
    }

    #summary {
        padding: 1;
        text-align: center;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self):
        """Initialize stats screen."""
        super().__init__()
        self.current_year = date.today().year

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Horizontal(
                Label(f"Viewing data for: {self.current_year}"),
                Button("Refresh", id="refresh-btn", variant="primary"),
                id="filter-bar",
            ),
            Static("Practitioner Statistics", classes="title"),
            Static(id="stats-content"),
            Static(id="summary"),
            id="stats-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load initial data when screen is displayed."""
        self._load_all_tabs()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "refresh-btn":
            self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh all statistics data."""
        self.app.notify("Refreshing statistics...", timeout=2)
        self._load_all_tabs()

    def _load_all_tabs(self) -> None:
        """Load data for practitioner statistics."""
        try:
            # Load config and create engine (SAME AS CLI)
            settings = load_config()
            db_path = get_database_path(settings)
            repository = BillRepository(db_path)
            engine = AnalyticsEngine(repository)

            # Create filter for current year
            filter_obj = BillFilter(year=self.current_year)

            # Load practitioner stats
            self._load_practitioner_stats(engine, filter_obj)

        except Exception as e:
            self.app.notify(
                f"Failed to load statistics: {e}",
                severity="error",
                timeout=5,
            )

    def _load_practitioner_stats(self, engine: AnalyticsEngine, filter_obj: BillFilter) -> None:
        """Load practitioner statistics (REUSE AnalyticsEngine).

        Args:
            engine: AnalyticsEngine instance
            filter_obj: Filter for year
        """
        try:
            # Get stats (SAME AS CLI)
            stats = engine.get_practitioner_stats(filter_obj, limit=20)

            # Get content container
            content = self.query_one("#stats-content", Static)

            # Create table content as formatted text
            if not stats:
                content.update("No data available for the selected year.")
            else:
                # Build table manually using Rich-style formatting
                table_lines = []
                table_lines.append("┌" + "─" * 100 + "┐")
                table_lines.append(f"│ {'Practitioner':<25} │ {'Type':<15} │ {'Visits':>7} │ {'Total':>12} │ {'Avg/Visit':>12} │ {'Last Visit':<12} │")
                table_lines.append("├" + "─" * 100 + "┤")

                for stat in stats:
                    practitioner = (stat.practitioner_name or "Unknown")[:25]
                    prac_type = (stat.practitioner_type or "-")[:15]
                    visits = str(stat.bill_count)
                    total = format_currency(float(stat.total_amount))
                    avg = format_currency(float(stat.average_amount))
                    last = stat.last_visit.strftime("%Y-%m-%d") if stat.last_visit else "-"

                    table_lines.append(f"│ {practitioner:<25} │ {prac_type:<15} │ {visits:>7} │ {total:>12} │ {avg:>12} │ {last:<12} │")

                table_lines.append("└" + "─" * 100 + "┘")
                content.update("\n".join(table_lines))

            # Update summary
            total = sum(s.total_amount for s in stats)
            total_visits = sum(s.bill_count for s in stats)
            summary = self.query_one("#summary", Static)
            summary.update(
                f"Showing {len(stats)} practitioner(s) | "
                f"Total visits: {total_visits} | "
                f"Combined total: {format_currency(float(total))}"
            )

        except Exception as e:
            self.app.notify(
                f"Failed to load practitioner stats: {e}",
                severity="error",
                timeout=5,
            )

    def _load_category_stats(self, engine: AnalyticsEngine, filter_obj: BillFilter) -> None:
        """Load category statistics (REUSE AnalyticsEngine).

        Args:
            engine: AnalyticsEngine instance
            filter_obj: Filter for year
        """
        try:
            # Get stats (SAME AS CLI)
            stats = engine.get_category_stats(filter_obj)

            # Get or create table in tab
            pane = self.query_one("#tab-category", TabPane)

            # Remove old table if exists
            old_tables = pane.query(DataTable)
            for table in old_tables:
                table.remove()

            # Create new table
            table = DataTable()
            table.add_columns(
                "Category",
                "Bills",
                "Total",
                "Avg/Bill",
                "% of Total",
                "Visual",
            )

            if not stats:
                table.add_row("No data", "-", "-", "-", "-", "-")
            else:
                for stat in stats:
                    # Create visual percentage bar
                    bar_length = int(stat.percentage_of_total / 5)  # 1 char = 5%
                    visual_bar = "█" * bar_length

                    # Mark major categories (>20%)
                    category_name = stat.category
                    if stat.is_major_category:
                        category_name = f"★ {category_name}"

                    table.add_row(
                        category_name,
                        str(stat.bill_count),
                        format_currency(float(stat.total_amount)),
                        format_currency(float(stat.average_amount)),
                        f"{stat.percentage_of_total:.1f}%",
                        visual_bar,
                    )

            pane.mount(table)

            # Update summary
            total = sum(s.total_amount for s in stats)
            total_bills = sum(s.bill_count for s in stats)
            summary = self.query_one("#summary", Static)
            summary.update(
                f"Showing {len(stats)} categories | "
                f"Total bills: {total_bills} | "
                f"Grand total: {format_currency(float(total))} | "
                f"★ = Major category (>20%)"
            )

        except Exception as e:
            self.app.notify(
                f"Failed to load category stats: {e}",
                severity="error",
                timeout=5,
            )

    def _load_monthly_stats(self, engine: AnalyticsEngine, filter_obj: BillFilter) -> None:
        """Load monthly statistics (REUSE AnalyticsEngine).

        Args:
            engine: AnalyticsEngine instance
            filter_obj: Filter for year
        """
        try:
            # Get stats (SAME AS CLI)
            stats = engine.get_monthly_stats(filter_obj)

            # Get or create table in tab
            pane = self.query_one("#tab-monthly", TabPane)

            # Remove old table if exists
            old_tables = pane.query(DataTable)
            for table in old_tables:
                table.remove()

            # Create new table
            table = DataTable()
            table.add_columns(
                "Period",
                "Month",
                "Bills",
                "Total",
                "Avg/Bill",
            )

            if not stats:
                table.add_row("No data", "-", "-", "-", "-")
            else:
                for stat in stats:
                    table.add_row(
                        stat.period,
                        stat.month_name,
                        str(stat.bill_count),
                        format_currency(float(stat.total_amount)),
                        format_currency(float(stat.average_amount)),
                    )

            pane.mount(table)

            # Update summary
            total = sum(s.total_amount for s in stats)
            total_bills = sum(s.bill_count for s in stats)
            avg_per_month = total / len(stats) if len(stats) > 0 else 0
            summary = self.query_one("#summary", Static)
            summary.update(
                f"Showing {len(stats)} months | "
                f"Total bills: {total_bills} | "
                f"Avg per month: {format_currency(float(avg_per_month))} | "
                f"Total: {format_currency(float(total))}"
            )

        except Exception as e:
            self.app.notify(
                f"Failed to load monthly stats: {e}",
                severity="error",
                timeout=5,
            )
