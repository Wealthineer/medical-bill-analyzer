"""Database connection management."""

import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Generator

from ..core.exceptions import DatabaseError
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Register adapters and converters for Decimal type
def adapt_decimal(value: Decimal) -> str:
    """Convert Decimal to string for SQLite storage."""
    return str(value)


def convert_decimal(value: bytes) -> Decimal:
    """Convert SQLite string back to Decimal."""
    return Decimal(value.decode())


# Register with sqlite3
sqlite3.register_adapter(Decimal, adapt_decimal)
sqlite3.register_converter("DECIMAL", convert_decimal)


class DatabaseConnection:
    """Manages SQLite database connections."""

    def __init__(self, db_path: Path):
        """
        Initialize database connection manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get database connection as context manager.

        Yields:
            SQLite connection

        Raises:
            DatabaseError: If connection fails

        Example:
            >>> with db.get_connection() as conn:
            ...     cursor = conn.execute("SELECT * FROM bills")
        """
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable foreign key support
            conn.execute("PRAGMA foreign_keys = ON")
            # Return rows as sqlite3.Row for dict-like access
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}") from e
        finally:
            if conn:
                conn.close()

    def execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement to execute
            parameters: Query parameters

        Returns:
            Cursor with results

        Raises:
            DatabaseError: If execution fails
        """
        with self.get_connection() as conn:
            return conn.execute(sql, parameters)

    def executemany(self, sql: str, parameters: list) -> sqlite3.Cursor:
        """
        Execute SQL statement with multiple parameter sets.

        Args:
            sql: SQL statement to execute
            parameters: List of parameter tuples

        Returns:
            Cursor with results

        Raises:
            DatabaseError: If execution fails
        """
        with self.get_connection() as conn:
            return conn.executemany(sql, parameters)

    def execute_script(self, sql_script: str):
        """
        Execute SQL script (multiple statements).

        Args:
            sql_script: SQL script to execute

        Raises:
            DatabaseError: If execution fails
        """
        with self.get_connection() as conn:
            conn.executescript(sql_script)

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                return cursor.fetchone() is not None
        except DatabaseError:
            return False

    def get_table_info(self, table_name: str) -> list:
        """
        Get table schema information.

        Args:
            table_name: Name of table

        Returns:
            List of column information dictionaries

        Raises:
            DatabaseError: If table doesn't exist
        """
        with self.get_connection() as conn:
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            return [dict(row) for row in cursor.fetchall()]
