"""Repository for application settings stored in database."""

from pathlib import Path
from typing import Optional

from .connection import DatabaseConnection
from ..config.settings import Settings, LLMConfig, AnthropicConfig, OpenAIConfig, OllamaConfig, BonusConfig, StorageConfig, ExtractionConfig


class SettingsRepository:
    """Repository for managing application settings in database.

    All app configuration is stored in a single row (id=1) in the settings table.
    This replaces the previous YAML-based configuration.
    """

    def __init__(self, db_path: Path):
        """Initialize repository.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def get_settings(self) -> Settings:
        """Get application settings from database.

        Returns:
            Settings object with all configuration

        Raises:
            ValueError: If settings not found in database
        """
        db = DatabaseConnection(self.db_path)
        with db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    llm_provider,
                    anthropic_model, anthropic_max_tokens, anthropic_temperature,
                    openai_model, openai_max_tokens, openai_temperature, openai_base_url,
                    ollama_model, ollama_base_url, ollama_timeout,
                    bonus_threshold, extract_line_items, retry_attempts,
                    database_path, pdf_storage_path
                FROM settings WHERE id = 1
                """
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError(
                    "Settings not found in database. "
                    "Please run 'medical-bill-analyzer setup' to initialize."
                )

            # Build Settings object from database row
            return Settings(
                llm=LLMConfig(
                    provider=row[0],
                    anthropic=AnthropicConfig(
                        model=row[1],
                        max_tokens=row[2],
                        temperature=row[3],
                    ),
                    openai=OpenAIConfig(
                        model=row[4],
                        max_tokens=row[5],
                        temperature=row[6],
                        base_url=row[7],  # Can be None
                    ),
                    ollama=OllamaConfig(
                        model=row[8],
                        base_url=row[9],
                        timeout=row[10],
                    ),
                ),
                bonus=BonusConfig(
                    default_threshold=row[11],
                ),
                extraction=ExtractionConfig(
                    extract_line_items=bool(row[12]),
                    retry_attempts=row[13],
                ),
                storage=StorageConfig(
                    database_path=Path(row[14]),
                    pdf_storage_path=Path(row[15]),
                ),
            )

    def save_settings(self, settings: Settings) -> None:
        """Save application settings to database.

        Args:
            settings: Settings object to save
        """
        db = DatabaseConnection(self.db_path)
        with db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO settings (
                    id,
                    llm_provider,
                    anthropic_model, anthropic_max_tokens, anthropic_temperature,
                    openai_model, openai_max_tokens, openai_temperature, openai_base_url,
                    ollama_model, ollama_base_url, ollama_timeout,
                    bonus_threshold, extract_line_items, retry_attempts,
                    database_path, pdf_storage_path
                ) VALUES (
                    1, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    settings.llm.provider,
                    settings.llm.anthropic.model,
                    settings.llm.anthropic.max_tokens,
                    settings.llm.anthropic.temperature,
                    settings.llm.openai.model,
                    settings.llm.openai.max_tokens,
                    settings.llm.openai.temperature,
                    settings.llm.openai.base_url,
                    settings.llm.ollama.model,
                    settings.llm.ollama.base_url,
                    settings.llm.ollama.timeout,
                    settings.bonus.default_threshold,
                    int(settings.extraction.extract_line_items),
                    settings.extraction.retry_attempts,
                    str(settings.storage.database_path),
                    str(settings.storage.pdf_storage_path),
                ),
            )

    def initialize_defaults(self, database_path: Path, pdf_storage_path: Path) -> None:
        """Initialize settings with default values.

        Called during setup wizard to create initial configuration.

        Args:
            database_path: Path to database file
            pdf_storage_path: Path to PDF storage directory
        """
        from ..config.defaults import (
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

        db = DatabaseConnection(self.db_path)
        with db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO settings (
                    id,
                    llm_provider,
                    anthropic_model, anthropic_max_tokens, anthropic_temperature,
                    openai_model, openai_max_tokens, openai_temperature, openai_base_url,
                    ollama_model, ollama_base_url, ollama_timeout,
                    bonus_threshold, extract_line_items, retry_attempts,
                    database_path, pdf_storage_path
                ) VALUES (
                    1, ?,
                    ?, ?, ?,
                    ?, ?, ?, NULL,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    DEFAULT_LLM_PROVIDER,
                    DEFAULT_ANTHROPIC_MODEL,
                    DEFAULT_MAX_TOKENS,
                    DEFAULT_TEMPERATURE,
                    DEFAULT_OPENAI_MODEL,
                    DEFAULT_MAX_TOKENS,
                    DEFAULT_TEMPERATURE,
                    DEFAULT_OLLAMA_MODEL,
                    DEFAULT_OLLAMA_HOST,
                    60,  # ollama timeout
                    DEFAULT_BONUS_THRESHOLD,
                    int(DEFAULT_EXTRACT_LINE_ITEMS),
                    DEFAULT_RETRY_ATTEMPTS,
                    str(database_path),
                    str(pdf_storage_path),
                ),
            )
