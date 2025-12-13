"""Repository pattern for database access."""

from .base import BaseRepository
from .bill_repository import BillRepository

__all__ = ["BaseRepository", "BillRepository"]
