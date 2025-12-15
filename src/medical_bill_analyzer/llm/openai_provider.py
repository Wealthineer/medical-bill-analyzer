"""OpenAI GPT provider for LLM-based bill extraction."""

import json
from typing import Any, Dict

from openai import OpenAI, APIError, APIConnectionError, RateLimitError

from ..core.exceptions import LLMExtractionError
from ..utils.logger import get_logger
from .base import LLMProvider
from .prompts import get_prompt

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """LLM provider implementation for OpenAI GPT models.

    This provider uses the OpenAI API to extract information from German
    medical bills using GPT models (e.g., gpt-4o-mini, gpt-4o).

    Example:
        >>> config = {
        ...     "model": "gpt-4o-mini",
        ...     "api_key": "sk-...",
        ...     "max_tokens": 1000,
        ...     "temperature": 0
        ... }
        >>> provider = OpenAIProvider(config)
        >>> result = provider.extract(bill_text)
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider.

        Args:
            config: Configuration dict with keys:
                - model: GPT model name (e.g., "gpt-4o-mini")
                - api_key: OpenAI API key
                - max_tokens: Maximum tokens in response (default: 1000)
                - temperature: Temperature for generation (default: 0)
        """
        super().__init__(config)

        api_key = config.get("api_key")
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.client = OpenAI(api_key=api_key)
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0)

        logger.info(
            f"OpenAI provider initialized with model={self.model}, "
            f"max_tokens={self.max_tokens}, temperature={self.temperature}"
        )

    def extract(self, bill_text: str, extraction_type: str = "basic") -> Dict[str, Any]:
        """Extract information from bill text using GPT.

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

            # Call OpenAI API
            logger.debug(f"Calling OpenAI API with model={self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            response_text = response.choices[0].message.content
            logger.debug(f"Received response: {response_text[:200]}...")

            # Parse JSON from response
            extracted_data = self._parse_json_response(response_text)

            logger.info(f"Successfully extracted data using {self.model}")
            return extracted_data

        except (APIError, APIConnectionError, RateLimitError) as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise LLMExtractionError(error_msg) from e

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON from GPT response: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Raw response: {response_text}")
            raise LLMExtractionError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error during extraction: {str(e)}"
            logger.error(error_msg)
            raise LLMExtractionError(error_msg) from e

    def test_connection(self) -> bool:
        """Test OpenAI API connection.

        Returns:
            True if connection succeeds, False otherwise
        """
        try:
            logger.info("Testing OpenAI API connection...")

            # Send minimal test request
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}],
            )

            # Check if we got a response
            if response and response.choices:
                logger.info("OpenAI API connection test successful")
                return True

            logger.warning("OpenAI API returned empty response")
            return False

        except (APIError, APIConnectionError) as e:
            logger.error(f"OpenAI API connection test failed: {str(e)}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error testing OpenAI connection: {str(e)}")
            return False

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from GPT response, handling common formatting issues.

        GPT sometimes wraps JSON in markdown code blocks or adds explanatory text.
        This method handles those cases.

        Args:
            response_text: Raw text response from GPT

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
