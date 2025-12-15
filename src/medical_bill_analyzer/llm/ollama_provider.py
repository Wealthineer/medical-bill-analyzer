"""Ollama provider for local LLM-based bill extraction."""

import json
from typing import Any, Dict

from ollama import Client, ResponseError

from ..core.exceptions import LLMExtractionError
from ..utils.logger import get_logger
from .base import LLMProvider
from .prompts import get_prompt

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider implementation for local Ollama models.

    This provider uses Ollama for completely local bill extraction with models
    like llama3.1, mistral, etc. No data is sent to external APIs.

    Example:
        >>> config = {
        ...     "model": "llama3.1:8b",
        ...     "base_url": "http://localhost:11434",
        ...     "options": {"temperature": 0}
        ... }
        >>> provider = OllamaProvider(config)
        >>> result = provider.extract(bill_text)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama provider.

        Args:
            config: Configuration dict with keys:
                - model: Ollama model name (e.g., "llama3.1:8b")
                - base_url: Ollama server URL (default: "http://localhost:11434")
                - options: Dict of Ollama options (temperature, etc.)
        """
        super().__init__(config)

        base_url = config.get("base_url", "http://localhost:11434")
        self.client = Client(host=base_url)
        self.options = config.get("options", {})

        # Set default temperature to 0 for deterministic extraction
        if "temperature" not in self.options:
            self.options["temperature"] = 0

        logger.info(
            f"Ollama provider initialized with model={self.model}, "
            f"base_url={base_url}, options={self.options}"
        )

    def extract(self, bill_text: str, extraction_type: str = "basic") -> Dict[str, Any]:
        """Extract information from bill text using local Ollama model.

        Args:
            bill_text: Raw text extracted from PDF
            extraction_type: Type of extraction ("basic" or "line_items")

        Returns:
            Dictionary with extracted data

        Raises:
            LLMExtractionError: If extraction fails
        """
        self._validate_bill_text(bill_text)
        self._log_extraction_attempt(bill_text, extraction_type)

        try:
            # Get formatted prompt
            prompt = get_prompt(extraction_type, bill_text)

            # Call Ollama API
            logger.debug(f"Calling Ollama with model={self.model}")
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options=self.options,
            )

            # Extract text from response
            response_text = response["response"]
            logger.debug(f"Received response: {response_text[:200]}...")

            # Parse JSON from response
            extracted_data = self._parse_json_response(response_text)

            logger.info(f"Successfully extracted data using {self.model}")
            return extracted_data

        except ResponseError as e:
            error_msg = f"Ollama API error: {str(e)}"
            logger.error(error_msg)
            raise LLMExtractionError(error_msg) from e

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON from Ollama response: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Raw response: {response_text}")
            raise LLMExtractionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during extraction: {str(e)}"
            logger.error(error_msg)
            raise LLMExtractionError(error_msg) from e

    def test_connection(self) -> bool:
        """Test Ollama server connection and model availability.

        Returns:
            True if connection succeeds and model is available, False otherwise
        """
        try:
            logger.info("Testing Ollama connection...")

            # List available models to test connection
            models = self.client.list()

            # Check if our model is available
            available_models = [m["name"] for m in models.get("models", [])]

            if self.model in available_models:
                logger.info(f"Ollama connection successful, model {self.model} available")
                return True

            logger.warning(
                f"Ollama connection successful but model {self.model} not found. "
                f"Available models: {', '.join(available_models)}"
            )
            return False

        except ResponseError as e:
            logger.error(f"Ollama connection test failed: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error testing Ollama connection: {str(e)}")
            return False

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Ollama response, handling common formatting issues.

        Local LLMs sometimes produce less consistent JSON output than cloud models.
        This method handles various formatting issues.

        Args:
            response_text: Raw text response from Ollama

        Returns:
            Parsed JSON as dictionary

        Raises:
            json.JSONDecodeError: If JSON parsing fails after cleanup attempts
        """
        # Try direct parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON from markdown code block
        if "```json" in response_text:
            # Extract content between ```json and ```
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end > start:
                json_str = response_text[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Try extracting JSON from any code block
        if "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end > start:
                json_str = response_text[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Try finding first { and last }
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # If all attempts fail, raise error with original text
        raise json.JSONDecodeError(
            f"Could not extract valid JSON from response",
            response_text,
            0,
        )
