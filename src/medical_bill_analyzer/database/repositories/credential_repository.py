"""Repository for credential database operations."""

from pathlib import Path
from typing import Optional

from ...core.exceptions import DatabaseError
from ...utils.logger import get_logger
from ..connection import DatabaseConnection

logger = get_logger(__name__)


class CredentialRepository:
    """Repository for managing LLM provider credentials."""

    def __init__(self, db_path: Path):
        """
        Initialize credential repository.

        Args:
            db_path: Path to SQLite database
        """
        self.db = DatabaseConnection(db_path)

    def save_credential(self, provider: str, api_key: Optional[str] = None) -> None:
        """
        Save or update credential for a provider.

        Args:
            provider: Provider name ('anthropic', 'openai', or 'ollama')
            api_key: API key (None for ollama which runs locally)

        Raises:
            DatabaseError: If save operation fails
        """
        try:
            with self.db.get_connection() as conn:
                # Use INSERT OR REPLACE to handle both create and update
                conn.execute(
                    """
                    INSERT OR REPLACE INTO credentials (provider, api_key, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (provider, api_key),
                )
                logger.info(f"Saved credential for provider: {provider}")

        except Exception as e:
            error_msg = f"Failed to save credential for {provider}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_credential(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider.

        Args:
            provider: Provider name ('anthropic', 'openai', or 'ollama')

        Returns:
            API key string, or None if not found

        Raises:
            DatabaseError: If query fails
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT api_key FROM credentials WHERE provider = ?",
                    (provider,),
                )
                row = cursor.fetchone()

                if row is None:
                    logger.debug(f"No credential found for provider: {provider}")
                    return None

                return row[0]

        except Exception as e:
            error_msg = f"Failed to get credential for {provider}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def has_credential(self, provider: str) -> bool:
        """
        Check if credential exists for a provider.

        Args:
            provider: Provider name

        Returns:
            True if credential exists, False otherwise

        Raises:
            DatabaseError: If query fails
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM credentials WHERE provider = ?",
                    (provider,),
                )
                count = cursor.fetchone()[0]
                return count > 0

        except Exception as e:
            error_msg = f"Failed to check credential for {provider}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_credential(self, provider: str) -> bool:
        """
        Delete credential for a provider.

        Args:
            provider: Provider name

        Returns:
            True if credential was deleted, False if not found

        Raises:
            DatabaseError: If delete operation fails
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM credentials WHERE provider = ?",
                    (provider,),
                )
                deleted = cursor.rowcount > 0

                if deleted:
                    logger.info(f"Deleted credential for provider: {provider}")
                else:
                    logger.debug(f"No credential to delete for provider: {provider}")

                return deleted

        except Exception as e:
            error_msg = f"Failed to delete credential for {provider}: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
