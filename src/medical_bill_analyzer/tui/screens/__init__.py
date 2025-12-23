"""TUI screens for Medical Bill Analyzer.

Each screen represents a different view in the application:
- Dashboard: Main overview with summary and recent bills
- Stats: Statistics with practitioner/category/monthly tabs
- Bills: List all bills with search functionality
- AddWizard: Multi-step wizard for adding PDF bills
"""

from .add_wizard import AddWizardScreen
from .bills import BillsScreen
from .dashboard import DashboardScreen
from .stats import StatsScreen

__all__ = [
    "DashboardScreen",
    "StatsScreen",
    "BillsScreen",
    "AddWizardScreen",
]
