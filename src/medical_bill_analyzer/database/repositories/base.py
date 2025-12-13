"""Base repository class with common CRUD operations."""

from abc import ABC
from pathlib import Path
from typing import Generic, List, Optional, Type, TypeVar

from ..connection import DatabaseConnection
from ..models import Bill

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository class.

    Provides common database operations that can be inherited
    by specific repository implementations.
    """

    def __init__(self, db_path: Path, model_class: Type[T]):
        """
        Initialize repository.

        Args:
            db_path: Path to SQLite database
            model_class: Pydantic model class for this repository
        """
        self.db = DatabaseConnection(db_path)
        self.model_class = model_class

    def _row_to_dict(self, row) -> dict:
        """
        Convert sqlite3.Row to dictionary.

        Args:
            row: sqlite3.Row object

        Returns:
            Dictionary with column names as keys
        """
        if row is None:
            return None
        return dict(row)

    def _rows_to_dicts(self, rows: List) -> List[dict]:
        """
        Convert list of sqlite3.Row objects to list of dictionaries.

        Args:
            rows: List of sqlite3.Row objects

        Returns:
            List of dictionaries
        """
        return [self._row_to_dict(row) for row in rows]
