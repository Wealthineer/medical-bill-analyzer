"""Tests for configuration settings."""

import pytest
from pathlib import Path
import yaml
import os

from medical_bill_analyzer.config.settings import (
    Settings,
    LLMConfig,
    StorageConfig,
    BonusConfig,
    ExtractionConfig,
    get_config_path,
    is_first_run,
)
from medical_bill_analyzer.config.defaults import get_user_config_dir


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test that default settings can be created."""
        settings = Settings()
        assert settings.llm.provider == "anthropic"
        assert settings.bonus.default_threshold == 1000.0
        assert settings.extraction.retry_attempts == 1
        assert settings.extraction.extract_line_items is False

    def test_settings_from_dict(self, sample_config_data):
        """Test creating settings from dictionary."""
        settings = Settings(**sample_config_data)
        assert settings.llm.provider == "anthropic"
        assert settings.llm.anthropic.model == "claude-sonnet-4-20250514"
        assert settings.bonus.default_threshold == 1000

    # Note: to_yaml and from_yaml methods were removed as part of the
    # settings refactor - settings are now stored in the database


class TestLLMConfig:
    """Test LLM configuration."""

    def test_anthropic_config(self):
        """Test Anthropic configuration."""
        config = LLMConfig(provider="anthropic")
        assert config.provider == "anthropic"
        assert config.anthropic.model == "claude-sonnet-4-20250514"
        # Note: API keys are now stored in database, not environment variables

    def test_openai_config(self):
        """Test OpenAI configuration."""
        config = LLMConfig(provider="openai")
        assert config.provider == "openai"
        assert config.openai.model == "gpt-4o-mini"

    def test_ollama_config(self):
        """Test Ollama configuration."""
        config = LLMConfig(provider="ollama")
        assert config.provider == "ollama"
        assert config.ollama.base_url == "http://localhost:11434"
        assert config.ollama.model == "llama3.1:8b"

    def test_get_provider_config_with_credentials(self, initialized_db):
        """Test get_provider_config loads credentials from database."""
        from medical_bill_analyzer.database.repositories import CredentialRepository

        # Setup: save credential to database
        credential_repo = CredentialRepository(initialized_db)
        credential_repo.save_credential("anthropic", "test-api-key-123")

        # Test: get provider config
        config = LLMConfig(provider="anthropic")
        provider_config = config.get_provider_config(credential_repo)

        assert provider_config["api_key"] == "test-api-key-123"
        assert provider_config["model"] == "claude-sonnet-4-20250514"

    def test_get_provider_config_missing_credentials(self, initialized_db):
        """Test get_provider_config raises error when credentials missing."""
        from medical_bill_analyzer.database.repositories import CredentialRepository

        credential_repo = CredentialRepository(initialized_db)

        config = LLMConfig(provider="anthropic")

        with pytest.raises(ValueError, match="API key not found"):
            config.get_provider_config(credential_repo)


class TestStorageConfig:
    """Test storage configuration."""

    def test_default_paths(self):
        """Test default storage paths."""
        config = StorageConfig()
        assert config.database_path.name == "medical_bills.db"
        assert config.pdf_storage_path.name == "pdfs"

    def test_relative_path_resolution(self):
        """Test that relative paths are resolved to user config dir."""
        config = StorageConfig(
            database_path="./data/test.db",
            pdf_storage_path="./data/pdfs/",
        )

        # Should be resolved relative to user config dir
        assert config.database_path.is_absolute()
        assert config.pdf_storage_path.is_absolute()


class TestConfigHelpers:
    """Test configuration helper functions."""

    def test_get_user_config_dir(self):
        """Test getting user config directory."""
        config_dir = get_user_config_dir()
        assert config_dir.name == ".medical-bill-analyzer"
        assert config_dir.is_absolute()

    def test_get_config_path(self):
        """Test getting config file path (now returns database path)."""
        config_path = get_config_path()
        assert config_path.name == "medical_bills.db"
        assert config_path.parent.name == "data"

    def test_is_first_run(self):
        """Test first run detection."""
        # This will depend on whether config actually exists
        # Just verify it returns a boolean
        result = is_first_run()
        assert isinstance(result, bool)
