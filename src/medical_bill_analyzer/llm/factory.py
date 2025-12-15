"""Factory for creating LLM provider instances.

This module implements the Factory pattern to instantiate the correct LLM
provider based on configuration, ensuring the application can work with
multiple LLM backends without tight coupling.
"""

from typing import Dict, Any

from ..core.exceptions import ProviderNotAvailableError
from ..utils.logger import get_logger
from .base import LLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider

logger = get_logger(__name__)


def create_llm_provider(provider_name: str, config: Dict[str, Any]) -> LLMProvider:
    """Create an LLM provider instance based on provider name.

    This factory function instantiates the correct provider class based on
    the provider name from configuration. It handles provider-specific
    initialization and error checking.

    Args:
        provider_name: Name of provider ("anthropic", "openai", or "ollama")
        config: Provider-specific configuration dictionary

    Returns:
        Initialized LLMProvider instance

    Raises:
        ProviderNotAvailableError: If provider name is invalid or provider
            cannot be initialized

    Example:
        >>> from medical_bill_analyzer.config.settings import load_settings
        >>> settings = load_settings()
        >>> provider = create_llm_provider(
        ...     settings.llm.provider,
        ...     settings.llm.get_provider_config()
        ... )
        >>> result = provider.extract(bill_text)
    """
    providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider,
    }

    provider_name_lower = provider_name.lower()

    if provider_name_lower not in providers:
        available = ", ".join(providers.keys())
        error_msg = (
            f"Unknown LLM provider: {provider_name}. "
            f"Available providers: {available}"
        )
        logger.error(error_msg)
        raise ProviderNotAvailableError(error_msg)

    provider_class = providers[provider_name_lower]

    try:
        logger.info(f"Creating {provider_name} provider...")
        provider = provider_class(config)
        logger.info(f"Successfully created {provider_name} provider")
        return provider

    except ValueError as e:
        # Handle missing API keys or invalid config
        error_msg = f"Failed to initialize {provider_name} provider: {str(e)}"
        logger.error(error_msg)
        raise ProviderNotAvailableError(error_msg) from e

    except ImportError as e:
        # Handle missing dependencies
        error_msg = (
            f"{provider_name} provider requires additional dependencies. "
            f"Install with: pip install {provider_name}"
        )
        logger.error(error_msg)
        raise ProviderNotAvailableError(error_msg) from e

    except Exception as e:
        error_msg = f"Unexpected error creating {provider_name} provider: {str(e)}"
        logger.error(error_msg)
        raise ProviderNotAvailableError(error_msg) from e


def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """List all available LLM providers with their metadata.

    Returns:
        Dictionary mapping provider names to their metadata:
        - description: Human-readable description
        - requires_api_key: Whether an API key is needed
        - default_models: List of commonly used models

    Example:
        >>> providers = list_available_providers()
        >>> for name, info in providers.items():
        ...     print(f"{name}: {info['description']}")
    """
    return {
        "anthropic": {
            "description": "Anthropic Claude models (cloud, paid)",
            "requires_api_key": True,
            "default_models": [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
            ],
            "privacy": "Data sent to Anthropic API",
        },
        "openai": {
            "description": "OpenAI GPT models (cloud, paid)",
            "requires_api_key": True,
            "default_models": [
                "gpt-4o-mini",
                "gpt-4o",
            ],
            "privacy": "Data sent to OpenAI API",
        },
        "ollama": {
            "description": "Local Ollama models (offline, free)",
            "requires_api_key": False,
            "default_models": [
                "llama3.1:8b",
                "mistral",
                "qwen2.5:7b",
            ],
            "privacy": "All data stays local",
        },
    }
