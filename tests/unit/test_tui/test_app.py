"""Tests for main TUI application."""

import pytest
from unittest.mock import Mock, patch

from medical_bill_analyzer.tui.app import MedicalBillAnalyzerTUI


class TestMedicalBillAnalyzerTUI:
    """Test main TUI application class."""

    def test_app_title(self):
        """Test app has correct title."""
        app = MedicalBillAnalyzerTUI()
        assert app.TITLE == "Medical Bill Analyzer"
        assert app.SUB_TITLE == "Analyze German PKV medical bills"

    def test_app_bindings_defined(self):
        """Test app has required key bindings."""
        app = MedicalBillAnalyzerTUI()
        binding_keys = [b.key for b in app.BINDINGS]

        assert "q" in binding_keys
        assert "d" in binding_keys
        assert "s" in binding_keys
        assert "b" in binding_keys
        assert "a" in binding_keys
        assert "c" in binding_keys
        assert "escape" in binding_keys

    def test_app_has_css(self):
        """Test app has CSS styling defined."""
        app = MedicalBillAnalyzerTUI()
        assert app.CSS is not None
        assert len(app.CSS) > 0

    def test_binding_descriptions(self):
        """Test bindings have descriptive labels."""
        app = MedicalBillAnalyzerTUI()
        binding_desc = {b.key: b.description for b in app.BINDINGS}

        assert binding_desc["q"] == "Quit"
        assert binding_desc["d"] == "Dashboard"
        assert binding_desc["s"] == "Statistics"
        assert binding_desc["b"] == "Bills"


class TestAppNavigationActions:
    """Test that navigation actions create correct screen types."""

    def test_action_show_dashboard_creates_dashboard_screen(self):
        """Test dashboard action creates DashboardScreen."""
        from medical_bill_analyzer.tui.screens.dashboard import DashboardScreen

        app = MedicalBillAnalyzerTUI()
        app.push_screen = Mock()

        app.action_show_dashboard()

        app.push_screen.assert_called_once()
        screen = app.push_screen.call_args[0][0]
        assert isinstance(screen, DashboardScreen)

    def test_action_show_stats_creates_stats_screen(self):
        """Test stats action creates StatsScreen."""
        from medical_bill_analyzer.tui.screens.stats import StatsScreen

        app = MedicalBillAnalyzerTUI()
        app.push_screen = Mock()

        app.action_show_stats()

        app.push_screen.assert_called_once()
        screen = app.push_screen.call_args[0][0]
        assert isinstance(screen, StatsScreen)

    def test_action_show_bills_creates_bills_screen(self):
        """Test bills action creates BillsScreen."""
        from medical_bill_analyzer.tui.screens.bills import BillsScreen

        app = MedicalBillAnalyzerTUI()
        app.push_screen = Mock()

        app.action_show_bills()

        app.push_screen.assert_called_once()
        screen = app.push_screen.call_args[0][0]
        assert isinstance(screen, BillsScreen)

    def test_action_show_add_wizard_creates_wizard_screen(self):
        """Test add wizard action creates AddWizardScreen."""
        from medical_bill_analyzer.tui.screens.add_wizard import AddWizardScreen

        app = MedicalBillAnalyzerTUI()
        app.push_screen = Mock()

        app.action_show_add_wizard()

        app.push_screen.assert_called_once()
        screen = app.push_screen.call_args[0][0]
        assert isinstance(screen, AddWizardScreen)

    def test_action_show_settings_creates_settings_screen(self):
        """Test settings action creates SettingsScreen."""
        from medical_bill_analyzer.tui.screens.settings import SettingsScreen

        app = MedicalBillAnalyzerTUI()
        app.push_screen = Mock()

        app.action_show_settings()

        app.push_screen.assert_called_once()
        screen = app.push_screen.call_args[0][0]
        assert isinstance(screen, SettingsScreen)

    def test_action_quit_calls_exit(self):
        """Test quit action exits the app."""
        app = MedicalBillAnalyzerTUI()
        app.exit = Mock()

        app.action_quit()

        app.exit.assert_called_once()


@pytest.mark.asyncio
class TestAppAsync:
    """Async tests using Textual's run_test."""

    async def test_app_starts_with_dashboard(self):
        """Test app starts and shows dashboard on mount."""
        app = MedicalBillAnalyzerTUI()

        # Patch is_first_run to return False (not first run, so dashboard shows)
        with patch("medical_bill_analyzer.config.settings.is_first_run", return_value=False):
            # Patch the data loading to avoid database access
            with patch("medical_bill_analyzer.tui.screens.dashboard.load_config"):
                with patch("medical_bill_analyzer.tui.screens.dashboard.get_database_path"):
                    with patch("medical_bill_analyzer.tui.screens.dashboard.BillRepository"):
                        with patch("medical_bill_analyzer.tui.screens.dashboard.BonusCalculator"):
                            async with app.run_test() as pilot:
                                # App should have started
                                assert app.is_running

                                # Should have at least one screen
                                assert len(app.screen_stack) >= 1
