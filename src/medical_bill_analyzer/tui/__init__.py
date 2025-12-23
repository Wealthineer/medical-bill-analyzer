"""Text User Interface (TUI) module for Medical Bill Analyzer.

This module provides an interactive terminal UI using Textual framework.
The TUI wraps existing business logic without duplication - it's purely
a presentation layer that calls the same core modules as the CLI.
"""

from .app import MedicalBillAnalyzerTUI

__all__ = ["MedicalBillAnalyzerTUI"]
