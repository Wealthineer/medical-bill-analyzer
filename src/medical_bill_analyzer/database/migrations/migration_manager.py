"""Database migration manager for applying schema updates."""

import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple

from ...core.exceptions import DatabaseError
from ...utils.logger import get_logger

logger = get_logger(__name__)


def get_migrations_dir() -> Path:
    """Get the migrations directory, handling PyInstaller bundled executables.

    Returns:
        Path to the migrations directory
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable (PyInstaller)
        base_path = Path(sys._MEIPASS)  # type: ignore
        return base_path / "medical_bill_analyzer" / "database" / "migrations"
    else:
        # Running in development
        return Path(__file__).parent


class MigrationManager:
    """Manages database schema migrations."""

    def __init__(self, db_path: Path):
        """
        Initialize migration manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.migrations_dir = get_migrations_dir()

    def get_current_version(self, conn: sqlite3.Connection) -> int:
        """
        Get current schema version from database.

        Args:
            conn: Database connection

        Returns:
            Current schema version (0 if no schema_version table exists)
        """
        try:
            cursor = conn.execute(
                "SELECT MAX(version) FROM schema_version"
            )
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # schema_version table doesn't exist yet
            return 0

    def get_available_migrations(self) -> List[Tuple[int, Path]]:
        """
        Get list of available migration files.

        Returns:
            List of (version, path) tuples sorted by version
        """
        migrations = []
        for sql_file in self.migrations_dir.glob("v*.sql"):
            # Extract version number from filename (e.g., v1_initial.sql -> 1)
            try:
                version = int(sql_file.stem.split("_")[0][1:])  # Remove 'v' prefix
                migrations.append((version, sql_file))
            except (ValueError, IndexError):
                logger.warning(f"Skipping invalid migration file: {sql_file.name}")
                continue

        return sorted(migrations, key=lambda x: x[0])

    def apply_migration(self, conn: sqlite3.Connection, version: int, sql_path: Path):
        """
        Apply a single migration.

        Args:
            conn: Database connection
            version: Migration version number
            sql_path: Path to SQL migration file

        Raises:
            DatabaseError: If migration fails
        """
        try:
            logger.info(f"Applying migration v{version}: {sql_path.name}")

            with open(sql_path, "r", encoding="utf-8") as f:
                sql = f.read()

            conn.executescript(sql)
            conn.commit()

            logger.info(f"Migration v{version} applied successfully")

        except sqlite3.Error as e:
            conn.rollback()
            raise DatabaseError(
                f"Failed to apply migration v{version}: {e}"
            ) from e
        except Exception as e:
            raise DatabaseError(
                f"Error reading migration file {sql_path}: {e}"
            ) from e

    def migrate(self) -> int:
        """
        Apply all pending migrations.

        Returns:
            Number of migrations applied

        Raises:
            DatabaseError: If any migration fails
        """
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            conn = sqlite3.connect(self.db_path)
            current_version = self.get_current_version(conn)
            available_migrations = self.get_available_migrations()

            if not available_migrations:
                logger.warning("No migration files found")
                return 0

            # Filter to only pending migrations
            pending = [
                (version, path)
                for version, path in available_migrations
                if version > current_version
            ]

            if not pending:
                logger.info(
                    f"Database schema is up to date (v{current_version})"
                )
                return 0

            logger.info(
                f"Current schema version: {current_version}, "
                f"applying {len(pending)} migration(s)"
            )

            for version, sql_path in pending:
                self.apply_migration(conn, version, sql_path)

            new_version = self.get_current_version(conn)
            logger.info(f"Migration complete. Schema version: {new_version}")

            conn.close()
            return len(pending)

        except sqlite3.Error as e:
            raise DatabaseError(f"Database error during migration: {e}") from e

    def initialize(self):
        """
        Initialize database with all migrations.

        This is a convenience method that creates the database
        and applies all migrations in one step.

        Raises:
            DatabaseError: If initialization fails
        """
        logger.info(f"Initializing database at {self.db_path}")
        migrations_applied = self.migrate()

        if migrations_applied > 0:
            logger.info(f"Database initialized with {migrations_applied} migration(s)")
        else:
            logger.info("Database already initialized")
