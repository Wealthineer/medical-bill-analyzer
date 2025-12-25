"""Main TUI application for Medical Bill Analyzer."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .screens.dashboard import DashboardScreen


class MedicalBillAnalyzerTUI(App):
    """Medical Bill Analyzer Text User Interface.

    An interactive terminal UI that provides a better user experience
    than CLI commands for regular use. The TUI calls the same core
    modules as CLI (BillProcessor, BonusCalculator, AnalyticsEngine)
    with zero business logic duplication.
    """

    TITLE = "Medical Bill Analyzer"
    SUB_TITLE = "Analyze German PKV medical bills"

    # CSS styling (optional - Textual provides good defaults)
    CSS = """
    Screen {
        background: $surface;
    }

    .title {
        text-style: bold;
        color: $accent;
    }

    DataTable {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "show_dashboard", "Dashboard"),
        Binding("s", "show_stats", "Statistics"),
        Binding("b", "show_bills", "Bills"),
        Binding("a", "show_add_wizard", "Add"),
        Binding("c", "show_settings", "Settings"),
        Binding("escape", "app.pop_screen", "Back", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts - launch dashboard."""
        self.push_screen(DashboardScreen())

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_show_dashboard(self) -> None:
        """Navigate to dashboard screen."""
        # Import here to avoid circular imports
        from .screens.dashboard import DashboardScreen

        self.push_screen(DashboardScreen())

    def action_show_stats(self) -> None:
        """Navigate to statistics screen."""
        # Lazy import to avoid errors if screen not yet implemented
        try:
            from .screens.stats import StatsScreen

            self.push_screen(StatsScreen())
        except ImportError:
            self.notify(
                "Statistics screen not yet implemented",
                severity="warning",
                timeout=3,
            )

    def action_show_bills(self) -> None:
        """Navigate to bills screen."""
        try:
            from .screens.bills import BillsScreen

            self.push_screen(BillsScreen())
        except ImportError:
            self.notify(
                "Bills screen not yet implemented",
                severity="warning",
                timeout=3,
            )

    def action_show_add_wizard(self) -> None:
        """Navigate to add bills wizard."""
        try:
            from .screens.add_wizard import AddWizardScreen

            self.push_screen(AddWizardScreen())
        except ImportError:
            self.notify(
                "Add wizard not yet implemented",
                severity="warning",
                timeout=3,
            )

    def action_show_settings(self) -> None:
        """Navigate to settings screen."""
        try:
            from .screens.settings import SettingsScreen

            self.push_screen(SettingsScreen())
        except ImportError:
            self.notify(
                "Settings screen not yet implemented",
                severity="warning",
                timeout=3,
            )
