"""Application settings using Pydantic."""

from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import os

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
    api_key_env: str = "ANTHROPIC_API_KEY"
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        return os.getenv(self.api_key_env)


class OpenAIConfig(BaseModel):
    """OpenAI GPT configuration."""

    model: str = DEFAULT_OPENAI_MODEL
    api_key_env: str = "OPENAI_API_KEY"
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE

    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        return os.getenv(self.api_key_env)


class OllamaConfig(BaseModel):
    """Ollama local LLM configuration."""

    host: str = DEFAULT_OLLAMA_HOST
    model: str = DEFAULT_OLLAMA_MODEL
    timeout: int = 60


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: Literal["anthropic", "openai", "ollama"] = DEFAULT_LLM_PROVIDER
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)


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
    )

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Settings":
        """Load settings from YAML file."""
        if not yaml_path.exists():
            # Return default settings if file doesn't exist
            return cls()

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)

    def to_yaml(self, yaml_path: Path) -> None:
        """Save settings to YAML file."""
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict, handling Path objects
        data = self.model_dump(mode="python")

        # Convert Path objects to strings for YAML serialization
        def convert_paths(obj):
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(v) for v in obj]
            elif isinstance(obj, Path):
                return str(obj)
            return obj

        data = convert_paths(data)

        with open(yaml_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return get_user_config_dir() / "config.yaml"


def is_first_run() -> bool:
    """Check if this is the first run (no config file exists)."""
    return not get_config_path().exists()


def get_settings() -> Settings:
    """Get application settings, loading from config file if it exists."""
    config_path = get_config_path()
    return Settings.from_yaml(config_path)


def save_settings(settings: Settings) -> None:
    """Save settings to config file."""
    config_path = get_config_path()
    settings.to_yaml(config_path)
