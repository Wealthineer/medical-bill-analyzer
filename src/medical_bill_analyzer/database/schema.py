"""Database schema management."""

from pathlib import Path

from ..core.exceptions import DatabaseError
from ..utils.logger import get_logger
from .connection import DatabaseConnection
from .migrations import MigrationManager

logger = get_logger(__name__)


def initialize_database(db_path: Path) -> bool:
    """
    Initialize database with schema.

    Args:
        db_path: Path to SQLite database file

    Returns:
        True if database was initialized, False if already initialized

    Raises:
        DatabaseError: If initialization fails
    """
    try:
        migration_manager = MigrationManager(db_path)
        migrations_applied = migration_manager.migrate()

        if migrations_applied > 0:
            logger.info(f"Database initialized with {migrations_applied} migration(s)")
            return True
        else:
            logger.info("Database already initialized")
            return False

    except Exception as e:
        raise DatabaseError(f"Failed to initialize database: {e}") from e


def verify_schema(db_path: Path) -> bool:
    """
    Verify that database schema is properly initialized.

    Args:
        db_path: Path to SQLite database file

    Returns:
        True if schema is valid, False otherwise
    """
    try:
        db = DatabaseConnection(db_path)

        # Check that required tables exist
        required_tables = ["schema_version", "bills"]

        for table in required_tables:
            if not db.table_exists(table):
                logger.error(f"Required table '{table}' does not exist")
                return False

        # Check schema version
        migration_manager = MigrationManager(db_path)
        with db.get_connection() as conn:
            current_version = migration_manager.get_current_version(conn)

        if current_version < 1:
            logger.error(f"Invalid schema version: {current_version}")
            return False

        logger.info(f"Database schema valid (v{current_version})")
        return True

    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def get_schema_version(db_path: Path) -> int:
    """
    Get current schema version.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Current schema version (0 if not initialized)
    """
    try:
        migration_manager = MigrationManager(db_path)
        db = DatabaseConnection(db_path)

        with db.get_connection() as conn:
            return migration_manager.get_current_version(conn)

    except Exception:
        return 0
