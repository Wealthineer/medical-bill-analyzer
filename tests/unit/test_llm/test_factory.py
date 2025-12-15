"""Tests for LLM provider factory."""

from unittest.mock import patch

import pytest

from medical_bill_analyzer.core.exceptions import ProviderNotAvailableError
from medical_bill_analyzer.llm.factory import create_llm_provider, list_available_providers
from medical_bill_analyzer.llm.anthropic_provider import AnthropicProvider
from medical_bill_analyzer.llm.openai_provider import OpenAIProvider
from medical_bill_analyzer.llm.ollama_provider import OllamaProvider


class TestCreateLLMProvider:
    """Test create_llm_provider factory function."""

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_create_anthropic_provider(self, mock_anthropic):
        """Test creating Anthropic provider."""
        config = {
            "model": "claude-sonnet-4-20250514",
            "api_key": "sk-ant-test",
        }

        provider = create_llm_provider("anthropic", config)

        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-sonnet-4-20250514"

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_create_anthropic_provider_case_insensitive(self, mock_anthropic):
        """Test provider name is case insensitive."""
        config = {
            "model": "claude-sonnet-4-20250514",
            "api_key": "sk-ant-test",
        }

        provider = create_llm_provider("ANTHROPIC", config)

        assert isinstance(provider, AnthropicProvider)

    @patch("medical_bill_analyzer.llm.openai_provider.OpenAI")
    def test_create_openai_provider(self, mock_openai):
        """Test creating OpenAI provider."""
        config = {
            "model": "gpt-4o-mini",
            "api_key": "sk-test",
        }

        provider = create_llm_provider("openai", config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4o-mini"

    @patch("medical_bill_analyzer.llm.ollama_provider.Client")
    def test_create_ollama_provider(self, mock_client):
        """Test creating Ollama provider."""
        config = {
            "model": "llama3.1:8b",
            "host": "http://localhost:11434",
        }

        provider = create_llm_provider("ollama", config)

        assert isinstance(provider, OllamaProvider)
        assert provider.model == "llama3.1:8b"

    def test_unknown_provider_raises_error(self):
        """Test unknown provider name raises error."""
        config = {"model": "test"}

        with pytest.raises(ProviderNotAvailableError) as exc:
            create_llm_provider("unknown_provider", config)

        assert "unknown" in str(exc.value).lower()
        assert "unknown_provider" in str(exc.value).lower()

    def test_missing_api_key_raises_error(self):
        """Test missing API key for cloud provider raises error."""
        config = {"model": "claude-sonnet-4-20250514"}

        with pytest.raises(ProviderNotAvailableError) as exc:
            create_llm_provider("anthropic", config)

        assert "api key" in str(exc.value).lower()


class TestListAvailableProviders:
    """Test list_available_providers function."""

    def test_returns_dict(self):
        """Test function returns dictionary."""
        providers = list_available_providers()

        assert isinstance(providers, dict)
        assert len(providers) > 0

    def test_contains_all_providers(self):
        """Test dictionary contains all expected providers."""
        providers = list_available_providers()

        assert "anthropic" in providers
        assert "openai" in providers
        assert "ollama" in providers

    def test_provider_metadata_structure(self):
        """Test each provider has required metadata fields."""
        providers = list_available_providers()

        for name, metadata in providers.items():
            assert "description" in metadata
            assert "requires_api_key" in metadata
            assert "default_models" in metadata
            assert "privacy" in metadata
            assert isinstance(metadata["description"], str)
            assert isinstance(metadata["requires_api_key"], bool)
            assert isinstance(metadata["default_models"], list)
            assert isinstance(metadata["privacy"], str)

    def test_anthropic_metadata(self):
        """Test Anthropic provider metadata is correct."""
        providers = list_available_providers()

        anthropic = providers["anthropic"]
        assert anthropic["requires_api_key"] is True
        assert len(anthropic["default_models"]) > 0
        assert "claude" in anthropic["default_models"][0].lower()
        assert "api" in anthropic["privacy"].lower()

    def test_openai_metadata(self):
        """Test OpenAI provider metadata is correct."""
        providers = list_available_providers()

        openai = providers["openai"]
        assert openai["requires_api_key"] is True
        assert len(openai["default_models"]) > 0
        assert "gpt" in openai["default_models"][0].lower()

    def test_ollama_metadata(self):
        """Test Ollama provider metadata is correct."""
        providers = list_available_providers()

        ollama = providers["ollama"]
        assert ollama["requires_api_key"] is False
        assert len(ollama["default_models"]) > 0
        assert "local" in ollama["privacy"].lower()
