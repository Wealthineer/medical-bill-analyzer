"""Application settings using Pydantic."""

from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .defaults import (
    get_user_config_dir,
    get_user_data_dir,
    DEFAULT_LLM_PROVIDER,
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_BONUS_THRESHOLD,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_EXTRACT_LINE_ITEMS,
)


class AnthropicConfig(BaseModel):
    """Anthropic Claude configuration."""

    model: str = DEFAULT_ANTHROPIC_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE


class OpenAIConfig(BaseModel):
    """OpenAI GPT configuration.

    Can be used with OpenAI API or compatible endpoints like LM Studio.
    """

    model: str = DEFAULT_OPENAI_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    base_url: str | None = None  # Optional: For LM Studio or other OpenAI-compatible endpoints


class OllamaConfig(BaseModel):
    """Ollama local LLM configuration."""

    base_url: str = DEFAULT_OLLAMA_HOST
    model: str = DEFAULT_OLLAMA_MODEL
    timeout: int = 60


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: Literal["anthropic", "openai", "ollama"] = DEFAULT_LLM_PROVIDER
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)

    def get_provider_config(self, credential_repo) -> dict:
        """Get the active provider's configuration with API key from database.

        Args:
            credential_repo: CredentialRepository instance for loading API keys

        Returns:
            Dict with provider-specific config including API key from database

        Raises:
            ValueError: If API key not found in database for cloud providers
        """
        if self.provider == "anthropic":
            config = self.anthropic.model_dump()
            api_key = credential_repo.get_credential("anthropic")
            if not api_key:
                raise ValueError(
                    "Anthropic API key not found in database. "
                    "Please run 'medical-bill-analyzer setup' to configure credentials."
                )
            config["api_key"] = api_key
            return config
        elif self.provider == "openai":
            config = self.openai.model_dump()
            api_key = credential_repo.get_credential("openai")
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found in database. "
                    "Please run 'medical-bill-analyzer setup' to configure credentials."
                )
            config["api_key"] = api_key
            return config
        else:  # ollama (local, no API key needed)
            return self.ollama.model_dump()


class StorageConfig(BaseModel):
    """Storage configuration."""

    database_path: Path = Field(default_factory=lambda: get_user_data_dir() / "medical_bills.db")
    pdf_storage_path: Path = Field(default_factory=lambda: get_user_data_dir() / "pdfs")

    @field_validator("database_path", "pdf_storage_path", mode="before")
    @classmethod
    def resolve_path(cls, v):
        """Resolve path relative to config directory if not absolute."""
        if isinstance(v, str):
            path = Path(v)
            if not path.is_absolute():
                # Relative to user config directory
                return get_user_config_dir() / path
            return path
        return v


class BonusConfig(BaseModel):
    """Bonus threshold configuration."""

    default_threshold: float = DEFAULT_BONUS_THRESHOLD


class ExtractionConfig(BaseModel):
    """Extraction configuration."""

    retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    extract_line_items: bool = DEFAULT_EXTRACT_LINE_ITEMS


class Settings(BaseSettings):
    """Main application settings."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    bonus: BonusConfig = Field(default_factory=BonusConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )



def get_config_path() -> Path:
    """Get the path to the database file.

    Note: This now returns the database path, not a config.yaml path.
    """
    return get_user_data_dir() / "medical_bills.db"


def is_first_run() -> bool:
    """Check if this is the first run (no settings in database)."""
    from ..database import SettingsRepository

    db_path = get_config_path()
    if not db_path.exists():
        return True

    try:
        repo = SettingsRepository(db_path)
        repo.get_settings()
        return False
    except ValueError:
        # Settings not found in database
        return True


def get_settings() -> Settings:
    """Get application settings from database.

    Returns:
        Settings object

    Raises:
        ValueError: If settings not found in database
    """
    from ..database import SettingsRepository

    db_path = get_config_path()
    repo = SettingsRepository(db_path)
    return repo.get_settings()


def save_settings(settings: Settings) -> None:
    """Save settings to database.

    Args:
        settings: Settings object to save
    """
    from ..database import SettingsRepository

    db_path = get_config_path()
    repo = SettingsRepository(db_path)
    repo.save_settings(settings)
