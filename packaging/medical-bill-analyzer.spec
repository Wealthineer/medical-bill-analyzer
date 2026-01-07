# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Medical Bill Analyzer.

This builds a standalone executable that includes all dependencies
and data files needed to run the application without Python installed.

Usage:
    pyinstaller packaging/medical-bill-analyzer.spec

Output:
    dist/medical-bill-analyzer (or .exe on Windows)
"""

import sys
from pathlib import Path

# Get the project root directory
spec_dir = Path(SPECPATH)
project_root = spec_dir.parent
src_dir = project_root / "src"

# Analysis - collect all imports and data files
a = Analysis(
    [str(src_dir / "medical_bill_analyzer" / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        # Bundle SQL migration files
        (
            str(src_dir / "medical_bill_analyzer" / "database" / "migrations" / "*.sql"),
            "medical_bill_analyzer/database/migrations"
        ),
    ],
    hiddenimports=[
        # LLM Providers
        "anthropic",
        "openai",
        "ollama",
        "httpx",
        "httpcore",
        "h11",
        "anyio",
        "sniffio",
        # PDF Processing
        "pdfplumber",
        "pdfminer",
        "pdfminer.pdfparser",
        "pdfminer.pdfdocument",
        "pdfminer.pdfpage",
        "pdfminer.pdfinterp",
        "pdfminer.converter",
        "pdfminer.layout",
        "PIL",
        "PIL._imaging",
        # TUI (Textual)
        "textual",
        "textual.app",
        "textual.widgets",
        "textual.screen",
        "textual.containers",
        "textual.css",
        "textual.css.query",
        "textual.driver",
        "textual.drivers",
        "textual.drivers.linux_driver",
        "textual.drivers.windows_driver",
        "rich",
        "rich.console",
        "rich.table",
        "rich.progress",
        "rich.panel",
        "rich.markup",
        "rich.syntax",
        # CLI
        "typer",
        "typer.main",
        "click",
        # Database
        "sqlite3",
        # Data validation
        "pydantic",
        "pydantic_core",
        "pydantic_settings",
        # Utilities
        "dateutil",
        "dateutil.parser",
        "tabulate",
        "yaml",
        # App modules
        "medical_bill_analyzer",
        "medical_bill_analyzer.main",
        "medical_bill_analyzer.cli",
        "medical_bill_analyzer.cli.app",
        "medical_bill_analyzer.cli.setup_cmd",
        "medical_bill_analyzer.cli.add_cmd",
        "medical_bill_analyzer.cli.list_cmd",
        "medical_bill_analyzer.cli.delete_cmd",
        "medical_bill_analyzer.cli.total_cmd",
        "medical_bill_analyzer.cli.bonus_cmd",
        "medical_bill_analyzer.cli.stats_cmd",
        "medical_bill_analyzer.tui",
        "medical_bill_analyzer.tui.app",
        "medical_bill_analyzer.tui.screens",
        "medical_bill_analyzer.tui.screens.dashboard",
        "medical_bill_analyzer.tui.screens.stats",
        "medical_bill_analyzer.tui.screens.bills",
        "medical_bill_analyzer.tui.screens.add_wizard",
        "medical_bill_analyzer.tui.screens.settings",
        "medical_bill_analyzer.config",
        "medical_bill_analyzer.config.settings",
        "medical_bill_analyzer.config.defaults",
        "medical_bill_analyzer.core",
        "medical_bill_analyzer.core.bill_processor",
        "medical_bill_analyzer.core.bonus_calculator",
        "medical_bill_analyzer.database",
        "medical_bill_analyzer.database.connection",
        "medical_bill_analyzer.database.models",
        "medical_bill_analyzer.database.repositories",
        "medical_bill_analyzer.database.settings_repository",
        "medical_bill_analyzer.database.migrations",
        "medical_bill_analyzer.database.migrations.migration_manager",
        "medical_bill_analyzer.extraction",
        "medical_bill_analyzer.extraction.extractor",
        "medical_bill_analyzer.llm",
        "medical_bill_analyzer.llm.factory",
        "medical_bill_analyzer.llm.anthropic_provider",
        "medical_bill_analyzer.llm.openai_provider",
        "medical_bill_analyzer.llm.ollama_provider",
        "medical_bill_analyzer.pdf",
        "medical_bill_analyzer.pdf.extractor",
        "medical_bill_analyzer.pdf.validator",
        "medical_bill_analyzer.analytics",
        "medical_bill_analyzer.analytics.engine",
        "medical_bill_analyzer.utils",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        "pytest",
        "pytest_cov",
        "pytest_asyncio",
        "coverage",
        # Exclude dev tools
        "black",
        "ruff",
        "mypy",
        "pyinstaller",
        # Exclude unused packages
        "tkinter",
        "unittest",
        "doctest",
    ],
    noarchive=False,
    optimize=1,
)

# Create the PYZ archive
pyz = PYZ(a.pure)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="medical-bill-analyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Terminal app (required for TUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon settings (uncomment when icons are available)
    # icon="packaging/assets/icon.ico" if sys.platform == "win32" else None,
)
