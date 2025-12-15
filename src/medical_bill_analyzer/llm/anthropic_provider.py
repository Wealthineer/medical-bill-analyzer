"""Anthropic Claude provider for LLM-based bill extraction."""

import json
from typing import Any, Dict

from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError

from ..core.exceptions import LLMExtractionError
from ..utils.logger import get_logger
from .base import LLMProvider
from .prompts import get_prompt

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """LLM provider implementation for Anthropic Claude models.

    This provider uses the Anthropic API to extract information from German
    medical bills using Claude models (e.g., claude-sonnet-4-20250514).

    Example:
        >>> config = {
        ...     "model": "claude-sonnet-4-20250514",
        ...     "api_key": "sk-ant-...",
        ...     "max_tokens": 1000,
        ...     "temperature": 0
        ... }
        >>> provider = AnthropicProvider(config)
        >>> result = provider.extract(bill_text)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider.

        Args:
            config: Configuration dict with keys:
                - model: Claude model name (e.g., "claude-sonnet-4-20250514")
                - api_key: Anthropic API key
                - max_tokens: Maximum tokens in response (default: 1000)
                - temperature: Temperature for generation (default: 0)
        """
        super().__init__(config)

        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("Anthropic API key is required")

        self.client = Anthropic(api_key=api_key)
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0)

        logger.info(
            f"Anthropic provider initialized with model={self.model}, "
            f"max_tokens={self.max_tokens}, temperature={self.temperature}"
        )

    def extract(self, bill_text: str, extraction_type: str = "basic") -> Dict[str, Any]:
        """Extract information from bill text using Claude.

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

            # Call Claude API
            logger.debug(f"Calling Anthropic API with model={self.model}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            response_text = response.content[0].text
            logger.debug(f"Received response: {response_text[:200]}...")

            # Parse JSON from response
            extracted_data = self._parse_json_response(response_text)

            logger.info(f"Successfully extracted data using {self.model}")
            return extracted_data

        except (APIError, APIConnectionError, RateLimitError) as e:
            error_msg = f"Anthropic API error: {str(e)}"
            logger.error(error_msg)
            raise LLMExtractionError(error_msg) from e

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON from Claude response: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Raw response: {response_text}")
            raise LLMExtractionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during extraction: {str(e)}"
            logger.error(error_msg)
            raise LLMExtractionError(error_msg) from e

    def test_connection(self) -> bool:
        """Test Anthropic API connection.

        Returns:
            True if connection succeeds, False otherwise
        """
        try:
            logger.info("Testing Anthropic API connection...")

            # Send minimal test request
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}],
            )

            # Check if we got a response
            if response and response.content:
                logger.info("Anthropic API connection test successful")
                return True

            logger.warning("Anthropic API returned empty response")
            return False

        except (APIError, APIConnectionError) as e:
            logger.error(f"Anthropic API connection test failed: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error testing Anthropic connection: {str(e)}")
            return False

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from Claude response, handling common formatting issues.

        Claude sometimes wraps JSON in markdown code blocks or adds explanatory text.
        This method handles those cases.

        Args:
            response_text: Raw text response from Claude

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
