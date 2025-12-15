"""Tests for LLM providers with mocked API calls."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from medical_bill_analyzer.core.exceptions import LLMExtractionError
from medical_bill_analyzer.llm.anthropic_provider import AnthropicProvider
from medical_bill_analyzer.llm.openai_provider import OpenAIProvider
from medical_bill_analyzer.llm.ollama_provider import OllamaProvider


# Sample German medical bill text for testing
SAMPLE_BILL_TEXT = """
Dr. med. Anna Müller
Fachärztin für Allgemeinmedizin
Hauptstraße 123, 10115 Berlin

Rechnung

Patient: Max Mustermann
Rechnungsnummer: 2024-001234
Rechnungsdatum: 15.03.2024

GOÄ-Ziffer 1 - Beratung: 10,72 EUR
GOÄ-Ziffer 5 - Untersuchung: 14,57 EUR

Gesamtbetrag: 29,49 EUR
"""

# Sample valid JSON response
SAMPLE_JSON_RESPONSE = {
    "practitioner_name": "Dr. med. Anna Müller",
    "practitioner_type": "Arzt",
    "bill_date": "2024-03-15",
    "bill_number": "2024-001234",
    "total_amount": 29.49,
    "currency": "EUR",
}


class TestAnthropicProvider:
    """Test Anthropic Claude provider."""

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_initialization(self, mock_anthropic):
        """Test provider initialization."""
        config = {
            "model": "claude-sonnet-4-20250514",
            "api_key": "sk-ant-test",
            "max_tokens": 1000,
            "temperature": 0,
        }

        provider = AnthropicProvider(config)

        assert provider.model == "claude-sonnet-4-20250514"
        assert provider.max_tokens == 1000
        assert provider.temperature == 0
        # Verify Anthropic client was initialized with API key
        mock_anthropic.assert_called_once_with(api_key="sk-ant-test")

    def test_initialization_missing_api_key_raises_error(self):
        """Test initialization without API key raises error."""
        config = {"model": "claude-sonnet-4-20250514"}

        with pytest.raises(ValueError) as exc:
            AnthropicProvider(config)

        assert "api key" in str(exc.value).lower()

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_extract_success(self, mock_anthropic):
        """Test successful extraction."""
        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps(SAMPLE_JSON_RESPONSE))]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        result = provider.extract(SAMPLE_BILL_TEXT)

        assert result["practitioner_name"] == "Dr. med. Anna Müller"
        assert result["total_amount"] == 29.49
        assert result["currency"] == "EUR"

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_extract_with_markdown_wrapped_json(self, mock_anthropic):
        """Test extraction handles JSON wrapped in markdown code blocks."""
        # Response with markdown code block
        response_text = f"```json\n{json.dumps(SAMPLE_JSON_RESPONSE)}\n```"

        mock_response = Mock()
        mock_response.content = [Mock(text=response_text)]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        result = provider.extract(SAMPLE_BILL_TEXT)

        assert result["practitioner_name"] == "Dr. med. Anna Müller"

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_extract_empty_text_raises_error(self, mock_anthropic):
        """Test extraction with empty text raises error."""
        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        with pytest.raises(ValueError) as exc:
            provider.extract("")

        assert "empty" in str(exc.value).lower()

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_extract_api_error_raises_llm_error(self, mock_anthropic):
        """Test API error is wrapped in LLMExtractionError."""
        # Simulate API error by raising an exception
        mock_anthropic.return_value.messages.create.side_effect = Exception("API connection failed")

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        with pytest.raises(LLMExtractionError) as exc:
            provider.extract(SAMPLE_BILL_TEXT)

        assert "error" in str(exc.value).lower()

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_extract_invalid_json_raises_error(self, mock_anthropic):
        """Test invalid JSON response raises error."""
        mock_response = Mock()
        mock_response.content = [Mock(text="This is not JSON")]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        with pytest.raises(LLMExtractionError) as exc:
            provider.extract(SAMPLE_BILL_TEXT)

        assert "json" in str(exc.value).lower()

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_test_connection_success(self, mock_anthropic):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.content = [Mock(text="test")]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        assert provider.test_connection() is True

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_test_connection_failure(self, mock_anthropic):
        """Test connection test failure."""
        # Simulate API connection failure
        mock_anthropic.return_value.messages.create.side_effect = Exception("Connection failed")

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        assert provider.test_connection() is False


class TestOpenAIProvider:
    """Test OpenAI GPT provider."""

    def test_initialization(self):
        """Test provider initialization."""
        config = {
            "model": "gpt-4o-mini",
            "api_key": "sk-test",
            "max_tokens": 1000,
            "temperature": 0,
        }

        provider = OpenAIProvider(config)

        assert provider.model == "gpt-4o-mini"
        assert provider.max_tokens == 1000
        assert provider.temperature == 0

    def test_initialization_missing_api_key_raises_error(self):
        """Test initialization without API key raises error."""
        config = {"model": "gpt-4o-mini"}

        with pytest.raises(ValueError) as exc:
            OpenAIProvider(config)

        assert "api key" in str(exc.value).lower()

    @patch("medical_bill_analyzer.llm.openai_provider.OpenAI")
    def test_extract_success(self, mock_openai):
        """Test successful extraction."""
        # Mock API response
        mock_message = Mock()
        mock_message.content = json.dumps(SAMPLE_JSON_RESPONSE)

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        mock_openai.return_value.chat.completions.create.return_value = mock_response

        config = {"model": "gpt-4o-mini", "api_key": "sk-test"}
        provider = OpenAIProvider(config)

        result = provider.extract(SAMPLE_BILL_TEXT)

        assert result["practitioner_name"] == "Dr. med. Anna Müller"
        assert result["total_amount"] == 29.49

    @patch("medical_bill_analyzer.llm.openai_provider.OpenAI")
    def test_test_connection_success(self, mock_openai):
        """Test successful connection test."""
        mock_message = Mock()
        mock_message.content = "test"

        mock_choice = Mock()
        mock_choice.message = mock_message

        mock_response = Mock()
        mock_response.choices = [mock_choice]

        mock_openai.return_value.chat.completions.create.return_value = mock_response

        config = {"model": "gpt-4o-mini", "api_key": "sk-test"}
        provider = OpenAIProvider(config)

        assert provider.test_connection() is True

    @patch("medical_bill_analyzer.llm.openai_provider.OpenAI")
    def test_test_connection_failure(self, mock_openai):
        """Test connection test failure."""
        # Simulate API connection failure
        mock_openai.return_value.chat.completions.create.side_effect = Exception("Connection failed")

        config = {"model": "gpt-4o-mini", "api_key": "sk-test"}
        provider = OpenAIProvider(config)

        assert provider.test_connection() is False


class TestOllamaProvider:
    """Test Ollama local LLM provider."""

    def test_initialization(self):
        """Test provider initialization."""
        config = {
            "model": "llama3.1:8b",
            "host": "http://localhost:11434",
            "options": {"temperature": 0},
        }

        provider = OllamaProvider(config)

        assert provider.model == "llama3.1:8b"
        assert provider.options["temperature"] == 0

    @patch("medical_bill_analyzer.llm.ollama_provider.Client")
    def test_initialization_default_host(self, mock_client):
        """Test provider uses default host if not specified."""
        config = {"model": "llama3.1:8b"}

        provider = OllamaProvider(config)

        # Verify Client was initialized with default localhost
        mock_client.assert_called_once_with(host="http://localhost:11434")

    def test_initialization_default_temperature(self):
        """Test temperature defaults to 0 for deterministic output."""
        config = {"model": "llama3.1:8b"}

        provider = OllamaProvider(config)

        assert provider.options["temperature"] == 0

    @patch("medical_bill_analyzer.llm.ollama_provider.Client")
    def test_extract_success(self, mock_client):
        """Test successful extraction."""
        # Mock API response
        mock_response = {"response": json.dumps(SAMPLE_JSON_RESPONSE)}
        mock_client.return_value.generate.return_value = mock_response

        config = {"model": "llama3.1:8b"}
        provider = OllamaProvider(config)

        result = provider.extract(SAMPLE_BILL_TEXT)

        assert result["practitioner_name"] == "Dr. med. Anna Müller"
        assert result["total_amount"] == 29.49

    @patch("medical_bill_analyzer.llm.ollama_provider.Client")
    def test_test_connection_success(self, mock_client):
        """Test successful connection test."""
        mock_models = {"models": [{"name": "llama3.1:8b"}]}
        mock_client.return_value.list.return_value = mock_models

        config = {"model": "llama3.1:8b"}
        provider = OllamaProvider(config)

        assert provider.test_connection() is True

    @patch("medical_bill_analyzer.llm.ollama_provider.Client")
    def test_test_connection_model_not_found(self, mock_client):
        """Test connection test when model is not available."""
        mock_models = {"models": [{"name": "different-model"}]}
        mock_client.return_value.list.return_value = mock_models

        config = {"model": "llama3.1:8b"}
        provider = OllamaProvider(config)

        assert provider.test_connection() is False

    @patch("medical_bill_analyzer.llm.ollama_provider.Client")
    def test_test_connection_failure(self, mock_client):
        """Test connection test failure."""
        from ollama import ResponseError

        mock_client.return_value.list.side_effect = ResponseError("Connection failed")

        config = {"model": "llama3.1:8b"}
        provider = OllamaProvider(config)

        assert provider.test_connection() is False


class TestJSONParsing:
    """Test JSON parsing across all providers."""

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_parse_json_with_explanation_text(self, mock_anthropic):
        """Test parsing JSON when LLM adds explanation text."""
        response_text = f"Here is the extracted information:\n{json.dumps(SAMPLE_JSON_RESPONSE)}"

        mock_response = Mock()
        mock_response.content = [Mock(text=response_text)]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        result = provider.extract(SAMPLE_BILL_TEXT)

        assert result["practitioner_name"] == "Dr. med. Anna Müller"

    @patch("medical_bill_analyzer.llm.anthropic_provider.Anthropic")
    def test_parse_json_with_code_block_no_language(self, mock_anthropic):
        """Test parsing JSON in code block without language specifier."""
        response_text = f"```\n{json.dumps(SAMPLE_JSON_RESPONSE)}\n```"

        mock_response = Mock()
        mock_response.content = [Mock(text=response_text)]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        config = {"model": "claude-sonnet-4-20250514", "api_key": "sk-ant-test"}
        provider = AnthropicProvider(config)

        result = provider.extract(SAMPLE_BILL_TEXT)

        assert result["practitioner_name"] == "Dr. med. Anna Müller"
