"""Default configuration values."""

from pathlib import Path
import sys
import os


def get_user_config_dir() -> Path:
    """
    Get the user configuration directory.

    Returns:
        Path: Configuration directory path
            - Linux/macOS: ~/.medical-bill-analyzer/
            - Windows: %APPDATA%/medical-bill-analyzer/
    """
    if sys.platform == "win32":
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home()
    return base / ".medical-bill-analyzer"


def get_user_data_dir() -> Path:
    """Get the user data directory (for database and PDFs)."""
    return get_user_config_dir() / "data"


def get_user_logs_dir() -> Path:
    """Get the user logs directory."""
    return get_user_config_dir() / "logs"


# Default configuration values
DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.0
DEFAULT_BONUS_THRESHOLD = 1000.0  # EUR
DEFAULT_RETRY_ATTEMPTS = 1
DEFAULT_EXTRACT_LINE_ITEMS = False

# Default configuration dictionary
DEFAULT_CONFIG = {
    "llm": {
        "provider": DEFAULT_LLM_PROVIDER,
        "anthropic": {
            "model": DEFAULT_ANTHROPIC_MODEL,
            "api_key_env": "ANTHROPIC_API_KEY",
            "max_tokens": DEFAULT_MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
        },
        "openai": {
            "model": DEFAULT_OPENAI_MODEL,
            "api_key_env": "OPENAI_API_KEY",
            "max_tokens": DEFAULT_MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
        },
        "ollama": {
            "model": DEFAULT_OLLAMA_MODEL,
            "base_url": DEFAULT_OLLAMA_HOST,
            "timeout": 60,
        },
    },
    "storage": {
        "database_path": str(get_user_data_dir() / "medical_bills.db"),
        "pdf_storage_path": str(get_user_data_dir() / "pdfs"),
    },
    "bonus": {
        "default_threshold": DEFAULT_BONUS_THRESHOLD,
    },
}
