"""Abstract base class for LLM providers.

This module defines the interface that all LLM providers must implement,
ensuring consistent behavior across different LLM backends (Anthropic, OpenAI, Ollama).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM provider implementations (Anthropic, OpenAI, Ollama) must inherit
    from this class and implement its abstract methods. This ensures a consistent
    interface for bill text extraction regardless of the underlying LLM.

    The provider is responsible for:
    - Sending bill text to the LLM API
    - Parsing the JSON response
    - Handling API errors and retries
    - Returning structured data that can be validated with Pydantic schemas
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the LLM provider with configuration.

        Args:
            config: Provider-specific configuration dict containing:
                - model: Model name/ID to use
                - api_key: API key (if cloud provider)
                - max_tokens: Maximum tokens in response
                - temperature: Temperature for generation (0 for deterministic)
                - Additional provider-specific settings
        """
        self.config = config
        self.model = config.get("model")
        logger.info(f"Initialized {self.__class__.__name__} with model: {self.model}")

    @abstractmethod
    def extract(self, bill_text: str, extraction_type: str = "basic") -> Dict[str, Any]:
        """Extract information from medical bill text.

        This is the main method that sends bill text to the LLM and returns
        structured data. The LLM response should be parsed as JSON and validated
        against the appropriate Pydantic schema.

        Args:
            bill_text: Raw text extracted from PDF medical bill
            extraction_type: Type of extraction to perform:
                - "basic": Extract practitioner, date, amount (Phase 1)
                - "line_items": Extract individual line items (Phase 3)

        Returns:
            Dictionary containing extracted data that can be validated with
            BasicExtractionResponse or LineItemExtractionResponse Pydantic model.

        Raises:
            LLMExtractionError: If extraction fails due to API error, parsing error,
                or validation error.

        Example:
            >>> provider = AnthropicProvider(config)
            >>> result = provider.extract(bill_text)
            >>> validated = BasicExtractionResponse(**result)
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the provider is accessible and configured correctly.

        This method should verify that:
        - API credentials are valid (for cloud providers)
        - The model is accessible
        - A simple test request succeeds

        Returns:
            True if connection test succeeds, False otherwise.

        Example:
            >>> provider = AnthropicProvider(config)
            >>> if provider.test_connection():
            ...     print("Provider is ready!")
        """
        pass

    def _validate_bill_text(self, bill_text: str) -> None:
        """Validate bill text before sending to LLM.

        Args:
            bill_text: Text to validate

        Raises:
            ValueError: If bill text is empty or too short
        """
        if not bill_text or not bill_text.strip():
            raise ValueError("Bill text cannot be empty")

        if len(bill_text.strip()) < 10:
            raise ValueError("Bill text is too short (minimum 10 characters)")

    def _log_extraction_attempt(self, bill_text: str, extraction_type: str) -> None:
        """Log extraction attempt for debugging.

        Args:
            bill_text: Bill text being processed
            extraction_type: Type of extraction
        """
        text_preview = bill_text[:100].replace("\n", " ")
        logger.info(
            f"Attempting {extraction_type} extraction with {self.__class__.__name__}. "
            f"Text preview: {text_preview}..."
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration.

        Returns:
            Dictionary containing model name, provider type, and settings.
        """
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
            "config": {k: v for k, v in self.config.items() if k != "api_key"},
        }
