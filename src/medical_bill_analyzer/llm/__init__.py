"""LLM provider abstraction layer for medical bill extraction.

This module provides a flexible abstraction for working with different LLM
providers (Anthropic Claude, OpenAI GPT, local Ollama) for extracting
information from German medical bills.

Example usage:
    >>> from medical_bill_analyzer.llm import create_llm_provider
    >>> from medical_bill_analyzer.llm.schemas import BasicExtractionResponse
    >>>
    >>> # Create provider from config
    >>> config = {
    ...     "model": "claude-sonnet-4-20250514",
    ...     "api_key": "sk-ant-...",
    ...     "max_tokens": 1000,
    ...     "temperature": 0
    ... }
    >>> provider = create_llm_provider("anthropic", config)
    >>>
    >>> # Extract information
    >>> result_dict = provider.extract(bill_text)
    >>> result = BasicExtractionResponse(**result_dict)
    >>> print(f"Practitioner: {result.practitioner_name}")
    >>> print(f"Total: {result.total_amount} {result.currency}")
"""

from .base import LLMProvider
from .factory import create_llm_provider, list_available_providers
from .schemas import BasicExtractionResponse, ExtractionError

__all__ = [
    "LLMProvider",
    "create_llm_provider",
    "list_available_providers",
    "BasicExtractionResponse",
    "ExtractionError",
]
