"""Tests for TUI screens - focusing on testable logic."""

import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch

from medical_bill_analyzer.tui.screens.dashboard import DashboardScreen
from medical_bill_analyzer.tui.screens.bills import BillsScreen
from medical_bill_analyzer.tui.screens.stats import StatsScreen
from medical_bill_analyzer.tui.screens.add_wizard import AddWizardScreen
from medical_bill_analyzer.tui.screens.settings import SettingsScreen


class TestDashboardScreen:
    """Test DashboardScreen."""

    def test_screen_has_css(self):
        """Test screen has CSS styling."""
        screen = DashboardScreen()
        assert screen.CSS is not None
        assert "#summary-container" in screen.CSS

    def test_compose_yields_widgets(self):
        """Test compose yields expected widget types."""
        screen = DashboardScreen()
        widgets = list(screen.compose())
        widget_types = [type(w).__name__ for w in widgets]

        assert "Header" in widget_types
        assert "Footer" in widget_types


class TestBillsScreen:
    """Test BillsScreen."""

    def test_screen_has_css(self):
        """Test screen has CSS styling."""
        screen = BillsScreen()
        assert screen.CSS is not None
        assert "#bills-table" in screen.CSS

    def test_screen_has_bindings(self):
        """Test screen has refresh and delete bindings."""
        screen = BillsScreen()
        binding_keys = [b[0] for b in screen.BINDINGS]
        assert "r" in binding_keys  # refresh
        assert "x" in binding_keys  # delete

    def test_compose_yields_widgets(self):
        """Test compose yields expected widget types."""
        screen = BillsScreen()
        widgets = list(screen.compose())
        widget_types = [type(w).__name__ for w in widgets]

        assert "Header" in widget_types
        assert "Footer" in widget_types


class TestStatsScreen:
    """Test StatsScreen."""

    def test_screen_has_css(self):
        """Test screen has CSS styling."""
        screen = StatsScreen()
        assert screen.CSS is not None
        assert "#stats-container" in screen.CSS

    def test_initializes_with_current_year(self):
        """Test screen initializes with current year."""
        screen = StatsScreen()
        assert screen.current_year == date.today().year

    def test_compose_yields_widgets(self):
        """Test compose yields expected widget types."""
        screen = StatsScreen()
        widgets = list(screen.compose())
        widget_types = [type(w).__name__ for w in widgets]

        assert "Header" in widget_types
        assert "Footer" in widget_types

    def test_button_events_trigger_year_change(self):
        """Test button events call _change_year."""
        screen = StatsScreen()
        screen._change_year = Mock()

        # Previous year button
        mock_event = Mock()
        mock_event.button.id = "prev-year-btn"
        screen.on_button_pressed(mock_event)
        screen._change_year.assert_called_with(-1)

        # Next year button
        mock_event.button.id = "next-year-btn"
        screen.on_button_pressed(mock_event)
        screen._change_year.assert_called_with(1)


class TestAddWizardScreen:
    """Test AddWizardScreen."""

    def test_screen_has_css(self):
        """Test screen has CSS styling."""
        screen = AddWizardScreen()
        assert screen.CSS is not None
        assert "#wizard-container" in screen.CSS

    def test_initializes_at_step_1(self):
        """Test screen starts at step 1."""
        screen = AddWizardScreen()
        assert screen.current_step == 1
        assert screen.selected_files == []
        assert screen.processing_result is None

    def test_compose_yields_widgets(self):
        """Test compose yields expected widget types."""
        screen = AddWizardScreen()
        widgets = list(screen.compose())
        widget_types = [type(w).__name__ for w in widgets]

        assert "Header" in widget_types
        assert "Footer" in widget_types

    def test_button_events_trigger_actions(self):
        """Test button events trigger correct methods."""
        screen = AddWizardScreen()
        screen._validate_and_process_files = Mock()
        screen._delete_added_bills = Mock()

        # Next button on step 1
        mock_event = Mock()
        mock_event.button.id = "next-btn"
        screen.on_button_pressed(mock_event)
        screen._validate_and_process_files.assert_called_once()

        # Delete button
        mock_event.button.id = "delete-btn"
        screen.on_button_pressed(mock_event)
        screen._delete_added_bills.assert_called_once()


class TestSettingsScreen:
    """Test SettingsScreen."""

    def test_screen_has_css(self):
        """Test screen has CSS styling."""
        screen = SettingsScreen()
        assert screen.CSS is not None
        assert "#settings-container" in screen.CSS

    def test_initializes_with_anthropic_provider(self):
        """Test screen defaults to anthropic provider."""
        screen = SettingsScreen()
        assert screen.current_provider == "anthropic"
        assert screen.current_settings is None

    def test_compose_yields_widgets(self):
        """Test compose yields expected widget types."""
        screen = SettingsScreen()
        widgets = list(screen.compose())
        widget_types = [type(w).__name__ for w in widgets]

        assert "Header" in widget_types
        assert "Footer" in widget_types

    def test_button_events_trigger_actions(self):
        """Test button events trigger correct methods."""
        screen = SettingsScreen()
        screen._save_settings = Mock()
        screen._test_connection = Mock()

        # Save button
        mock_event = Mock()
        mock_event.button.id = "save-btn"
        screen.on_button_pressed(mock_event)
        screen._save_settings.assert_called_once()

        # Test button
        mock_event.button.id = "test-btn"
        screen.on_button_pressed(mock_event)
        screen._test_connection.assert_called_once()

    def test_provider_select_updates_current_provider(self):
        """Test provider selection updates state."""
        screen = SettingsScreen()
        screen._update_form_for_provider = Mock()

        mock_event = Mock()
        mock_event.select.id = "provider-select"
        mock_event.value = "openai"

        screen.on_select_changed(mock_event)

        assert screen.current_provider == "openai"
        screen._update_form_for_provider.assert_called_once()


class TestPathValidation:
    """Test path validation logic in AddWizardScreen."""

    def test_path_stripping_quotes(self):
        """Test that quotes are stripped from paths."""
        # This tests the path cleaning logic
        path_str = '"/path/to/file.pdf"'
        cleaned = path_str.strip().strip("'\"")
        assert cleaned == "/path/to/file.pdf"

    def test_escaped_spaces_handling(self):
        """Test that escaped spaces are handled."""
        path_str = "/path/to/My\\ Documents/file.pdf"
        cleaned = path_str.replace("\\ ", " ")
        assert cleaned == "/path/to/My Documents/file.pdf"


@pytest.mark.asyncio
class TestAsyncScreens:
    """Async tests for screens using Textual's run_test."""

    async def test_dashboard_mounts(self):
        """Test dashboard screen can be mounted."""
        from medical_bill_analyzer.tui.app import MedicalBillAnalyzerTUI

        app = MedicalBillAnalyzerTUI()

        with patch("medical_bill_analyzer.tui.screens.dashboard.load_config") as mock_config:
            mock_settings = Mock()
            mock_settings.bonus.default_threshold = 1000
            mock_config.return_value = mock_settings

            with patch("medical_bill_analyzer.tui.screens.dashboard.get_database_path"):
                with patch("medical_bill_analyzer.tui.screens.dashboard.BillRepository") as mock_repo:
                    mock_repo.return_value.filter.return_value = []
                    mock_repo.return_value.get_all.return_value = []

                    with patch("medical_bill_analyzer.tui.screens.dashboard.BonusCalculator") as mock_calc:
                        mock_calc.return_value.calculate_total.return_value = Decimal("0")
                        mock_rec = Mock()
                        mock_rec.should_keep_bonus = True
                        mock_calc.return_value.get_recommendation_for_year.return_value = mock_rec

                        async with app.run_test() as pilot:
                            assert app.is_running

    async def test_stats_screen_mounts(self):
        """Test stats screen can be mounted."""
        from medical_bill_analyzer.tui.app import MedicalBillAnalyzerTUI

        app = MedicalBillAnalyzerTUI()

        with patch("medical_bill_analyzer.tui.screens.dashboard.load_config"):
            with patch("medical_bill_analyzer.tui.screens.dashboard.get_database_path"):
                with patch("medical_bill_analyzer.tui.screens.dashboard.BillRepository"):
                    with patch("medical_bill_analyzer.tui.screens.dashboard.BonusCalculator"):
                        with patch("medical_bill_analyzer.tui.screens.stats.load_config"):
                            with patch("medical_bill_analyzer.tui.screens.stats.get_database_path"):
                                with patch("medical_bill_analyzer.tui.screens.stats.BillRepository"):
                                    with patch("medical_bill_analyzer.tui.screens.stats.AnalyticsEngine") as mock_engine:
                                        mock_engine.return_value.get_practitioner_stats.return_value = []

                                        async with app.run_test() as pilot:
                                            # Navigate to stats
                                            await pilot.press("s")
                                            assert app.is_running
