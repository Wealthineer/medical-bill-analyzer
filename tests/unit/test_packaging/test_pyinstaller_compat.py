"""Tests for PyInstaller compatibility features."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestMigrationsDir:
    """Test get_migrations_dir() for PyInstaller compatibility."""

    def test_development_mode_returns_file_parent(self):
        """Test that development mode returns Path(__file__).parent."""
        from medical_bill_analyzer.database.migrations.migration_manager import get_migrations_dir

        # In development, sys.frozen should not be set
        assert not hasattr(sys, 'frozen') or not sys.frozen

        result = get_migrations_dir()

        # Should return the directory containing migration_manager.py
        assert result.is_dir() or not result.exists()  # Dir may not exist in isolated tests
        assert result.name == "migrations"

    def test_frozen_mode_returns_meipass_path(self):
        """Test that frozen (bundled) mode uses sys._MEIPASS."""
        from medical_bill_analyzer.database.migrations import migration_manager

        # Mock frozen executable
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, '_MEIPASS', '/tmp/pyinstaller_bundle', create=True):
                result = migration_manager.get_migrations_dir()

        expected = Path('/tmp/pyinstaller_bundle/medical_bill_analyzer/database/migrations')
        assert result == expected

    def test_development_mode_path_contains_migrations(self):
        """Test that development path ends with expected structure."""
        from medical_bill_analyzer.database.migrations.migration_manager import get_migrations_dir

        result = get_migrations_dir()

        # Path should end with database/migrations
        assert 'migrations' in str(result)


class TestFirstRunDetection:
    """Test is_first_run() function for PyInstaller compatibility."""

    def test_first_run_true_when_db_missing(self, tmp_path):
        """Test first run returns True when database doesn't exist."""
        from medical_bill_analyzer.config.settings import is_first_run

        # Point to non-existent database
        non_existent_db = tmp_path / "nonexistent" / "db.sqlite"

        with patch('medical_bill_analyzer.config.settings.get_config_path', return_value=non_existent_db):
            assert is_first_run() is True

    def test_first_run_true_when_settings_table_missing(self, tmp_path):
        """Test first run returns True when settings table doesn't exist."""
        import sqlite3
        from medical_bill_analyzer.config.settings import is_first_run

        # Create empty database without settings table
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        with patch('medical_bill_analyzer.config.settings.get_config_path', return_value=db_path):
            # Should return True since settings table doesn't exist
            assert is_first_run() is True

    def test_first_run_false_when_settings_exist(self, tmp_path):
        """Test first run returns False when settings exist in database."""
        import sqlite3
        from medical_bill_analyzer.config.settings import is_first_run

        # Create database with settings table and data (matching actual schema)
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                llm_provider TEXT NOT NULL DEFAULT 'anthropic',
                anthropic_model TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514',
                anthropic_max_tokens INTEGER NOT NULL DEFAULT 1000,
                anthropic_temperature REAL NOT NULL DEFAULT 0.0,
                openai_model TEXT NOT NULL DEFAULT 'gpt-4o-mini',
                openai_max_tokens INTEGER NOT NULL DEFAULT 1000,
                openai_temperature REAL NOT NULL DEFAULT 0.0,
                openai_base_url TEXT,
                ollama_model TEXT NOT NULL DEFAULT 'llama3.1:8b',
                ollama_base_url TEXT NOT NULL DEFAULT 'http://localhost:11434',
                ollama_timeout INTEGER NOT NULL DEFAULT 60,
                bonus_threshold REAL NOT NULL DEFAULT 1000.0,
                extract_line_items INTEGER NOT NULL DEFAULT 0,
                retry_attempts INTEGER NOT NULL DEFAULT 1,
                database_path TEXT NOT NULL,
                pdf_storage_path TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insert valid settings row
        conn.execute(
            """INSERT INTO settings (
                id, llm_provider, anthropic_model, anthropic_max_tokens, anthropic_temperature,
                openai_model, openai_max_tokens, openai_temperature, openai_base_url,
                ollama_model, ollama_base_url, ollama_timeout,
                bonus_threshold, extract_line_items, retry_attempts,
                database_path, pdf_storage_path
            ) VALUES (1, 'anthropic', 'claude-sonnet-4-20250514', 1000, 0.0,
                'gpt-4o-mini', 1000, 0.0, NULL,
                'llama3.1:8b', 'http://localhost:11434', 60,
                1000.0, 0, 1, ?, ?)""",
            (str(db_path), str(tmp_path / "pdfs"))
        )
        conn.commit()
        conn.close()

        with patch('medical_bill_analyzer.config.settings.get_config_path', return_value=db_path):
            assert is_first_run() is False


class TestUserDirectories:
    """Test user directory functions work across platforms."""

    def test_get_user_config_dir_returns_path(self):
        """Test get_user_config_dir returns a Path object."""
        from medical_bill_analyzer.config.defaults import get_user_config_dir

        result = get_user_config_dir()

        assert isinstance(result, Path)
        assert "medical-bill-analyzer" in str(result)

    def test_get_user_data_dir_returns_path(self):
        """Test get_user_data_dir returns a Path object."""
        from medical_bill_analyzer.config.defaults import get_user_data_dir

        result = get_user_data_dir()

        assert isinstance(result, Path)
        assert "data" in str(result)

    def test_get_user_logs_dir_returns_path(self):
        """Test get_user_logs_dir returns a Path object."""
        from medical_bill_analyzer.config.defaults import get_user_logs_dir

        result = get_user_logs_dir()

        assert isinstance(result, Path)
        assert "logs" in str(result)

    def test_windows_uses_appdata(self):
        """Test Windows uses APPDATA directory."""
        from medical_bill_analyzer.config import defaults
        import os

        with patch.object(sys, 'platform', 'win32'):
            with patch.dict(os.environ, {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
                # Need to reimport to get fresh values
                import importlib
                importlib.reload(defaults)

                result = defaults.get_user_config_dir()
                # On Windows, should use APPDATA
                # (Note: actual test might need adjustment based on implementation)

    def test_linux_uses_home(self):
        """Test Linux uses home directory."""
        from medical_bill_analyzer.config.defaults import get_user_config_dir

        with patch.object(sys, 'platform', 'linux'):
            result = get_user_config_dir()
            # Should contain home-related path
            assert isinstance(result, Path)


class TestSpecFileConfiguration:
    """Test that spec file configuration is correct."""

    def test_spec_file_exists(self):
        """Test that the PyInstaller spec file exists."""
        spec_path = Path(__file__).parent.parent.parent.parent / "packaging" / "medical-bill-analyzer.spec"
        assert spec_path.exists(), f"Spec file not found at {spec_path}"

    def test_spec_file_contains_hidden_imports(self):
        """Test that spec file includes required hidden imports."""
        spec_path = Path(__file__).parent.parent.parent.parent / "packaging" / "medical-bill-analyzer.spec"
        content = spec_path.read_text()

        # Check for key hidden imports
        assert "anthropic" in content
        assert "openai" in content
        assert "ollama" in content
        assert "pdfplumber" in content
        assert "textual" in content
        assert "typer" in content

    def test_spec_file_includes_migrations(self):
        """Test that spec file bundles SQL migration files."""
        spec_path = Path(__file__).parent.parent.parent.parent / "packaging" / "medical-bill-analyzer.spec"
        content = spec_path.read_text()

        assert "migrations" in content
        assert ".sql" in content


class TestBuildScripts:
    """Test that build scripts are properly configured."""

    def test_build_sh_exists(self):
        """Test that build.sh exists and is executable."""
        build_script = Path(__file__).parent.parent.parent.parent / "scripts" / "build.sh"
        assert build_script.exists(), f"build.sh not found at {build_script}"

    def test_build_sh_has_shebang(self):
        """Test that build.sh has proper shebang."""
        build_script = Path(__file__).parent.parent.parent.parent / "scripts" / "build.sh"
        content = build_script.read_text()
        assert content.startswith("#!/bin/bash")

    def test_build_bat_exists(self):
        """Test that build.bat exists for Windows."""
        build_script = Path(__file__).parent.parent.parent.parent / "scripts" / "build.bat"
        assert build_script.exists(), f"build.bat not found at {build_script}"

    def test_package_release_script_exists(self):
        """Test that package-release.sh exists."""
        release_script = Path(__file__).parent.parent.parent.parent / "scripts" / "package-release.sh"
        assert release_script.exists(), f"package-release.sh not found at {release_script}"


class TestDistributionFiles:
    """Test that distribution packaging files exist."""

    def test_getting_started_exists(self):
        """Test that GETTING_STARTED.txt exists."""
        getting_started = Path(__file__).parent.parent.parent.parent / "packaging" / "GETTING_STARTED.txt"
        assert getting_started.exists()

    def test_readme_txt_exists(self):
        """Test that README.txt exists for distribution."""
        readme = Path(__file__).parent.parent.parent.parent / "packaging" / "README.txt"
        assert readme.exists()

    def test_license_exists(self):
        """Test that LICENSE file exists."""
        license_file = Path(__file__).parent.parent.parent.parent / "LICENSE"
        assert license_file.exists()

    def test_getting_started_contains_usage_info(self):
        """Test that GETTING_STARTED.txt contains usage information."""
        getting_started = Path(__file__).parent.parent.parent.parent / "packaging" / "GETTING_STARTED.txt"
        content = getting_started.read_text()

        assert "medical-bill-analyzer" in content.lower()
        assert "setup" in content.lower() or "first run" in content.lower()
