"""Tests for database migration system."""

from pathlib import Path

import pytest

from medical_bill_analyzer.core.exceptions import DatabaseError
from medical_bill_analyzer.database.connection import DatabaseConnection
from medical_bill_analyzer.database.migrations import MigrationManager
from medical_bill_analyzer.database.schema import (
    get_schema_version,
    initialize_database,
    verify_schema,
)


class TestMigrationManager:
    """Test MigrationManager class."""

    def test_get_current_version_no_table(self, test_db_path):
        """Test get_current_version returns 0 when no schema_version table."""
        db = DatabaseConnection(test_db_path)
        manager = MigrationManager(test_db_path)

        with db.get_connection() as conn:
            version = manager.get_current_version(conn)

        assert version == 0

    def test_get_current_version_with_table(self, initialized_db):
        """Test get_current_version returns correct version."""
        db = DatabaseConnection(initialized_db)
        manager = MigrationManager(initialized_db)

        with db.get_connection() as conn:
            version = manager.get_current_version(conn)

        # After initialization, all available migrations are applied (v1 and v2)
        assert version == 2

    def test_get_available_migrations(self, test_db_path):
        """Test get_available_migrations finds migration files."""
        manager = MigrationManager(test_db_path)
        migrations = manager.get_available_migrations()

        assert len(migrations) >= 1
        # Should find v1_initial.sql
        versions = [v for v, _ in migrations]
        assert 1 in versions

    def test_migrations_sorted_by_version(self, test_db_path):
        """Test migrations are returned in version order."""
        manager = MigrationManager(test_db_path)
        migrations = manager.get_available_migrations()

        versions = [v for v, _ in migrations]
        assert versions == sorted(versions)

    def test_apply_migration(self, test_db_path):
        """Test apply_migration creates tables."""
        db = DatabaseConnection(test_db_path)
        manager = MigrationManager(test_db_path)
        migrations = manager.get_available_migrations()

        # Apply first migration
        version, sql_path = migrations[0]

        with db.get_connection() as conn:
            manager.apply_migration(conn, version, sql_path)

        # Verify tables created
        assert db.table_exists("schema_version")
        assert db.table_exists("bills")

    def test_migrate_new_database(self, test_db_path):
        """Test migrate on new database applies all migrations."""
        manager = MigrationManager(test_db_path)

        count = manager.migrate()

        assert count >= 2  # Should apply v1 and v2 migrations
        assert Path(test_db_path).exists()

        # Verify schema version updated to latest
        db = DatabaseConnection(test_db_path)
        with db.get_connection() as conn:
            version = manager.get_current_version(conn)
        assert version == 2

    def test_migrate_already_migrated(self, initialized_db):
        """Test migrate on already migrated database does nothing."""
        manager = MigrationManager(initialized_db)

        count = manager.migrate()

        assert count == 0

    def test_initialize_creates_database(self, test_db_path):
        """Test initialize creates database and applies migrations."""
        manager = MigrationManager(test_db_path)

        manager.initialize()

        assert Path(test_db_path).exists()

        db = DatabaseConnection(test_db_path)
        assert db.table_exists("schema_version")
        assert db.table_exists("bills")

    def test_migration_creates_indexes(self, test_db_path):
        """Test migration creates indexes."""
        manager = MigrationManager(test_db_path)
        manager.migrate()

        db = DatabaseConnection(test_db_path)

        # Check indexes exist
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            "idx_bill_date",
            "idx_practitioner_name",
            "idx_practitioner_type",
            "idx_file_hash",
            "idx_extraction_status",
        ]

        for index in expected_indexes:
            assert index in indexes

    def test_migration_rollback_on_error(self, test_db_path, tmp_path):
        """Test migration rolls back on error."""
        # Create invalid migration file
        bad_migration = tmp_path / "v999_bad.sql"
        bad_migration.write_text("INVALID SQL SYNTAX;")

        # Temporarily add to migrations directory
        manager = MigrationManager(test_db_path)
        original_dir = manager.migrations_dir

        try:
            # Point to temp directory with bad migration
            manager.migrations_dir = tmp_path

            with pytest.raises(DatabaseError):
                manager.migrate()

        finally:
            manager.migrations_dir = original_dir


class TestSchemaFunctions:
    """Test schema.py helper functions."""

    def test_initialize_database(self, test_db_path):
        """Test initialize_database function."""
        result = initialize_database(test_db_path)

        assert result is True  # First run should initialize
        assert Path(test_db_path).exists()

        db = DatabaseConnection(test_db_path)
        assert db.table_exists("schema_version")
        assert db.table_exists("bills")

    def test_initialize_database_already_initialized(self, initialized_db):
        """Test initialize_database on already initialized database."""
        result = initialize_database(initialized_db)

        assert result is False  # Already initialized

    def test_verify_schema_valid(self, initialized_db):
        """Test verify_schema returns True for valid schema."""
        result = verify_schema(initialized_db)

        assert result is True

    def test_verify_schema_missing_tables(self, test_db_path):
        """Test verify_schema returns False for missing tables."""
        # Create database but don't initialize
        db = DatabaseConnection(test_db_path)
        db.execute("CREATE TABLE dummy (id INTEGER)")

        result = verify_schema(test_db_path)

        assert result is False

    def test_verify_schema_no_database(self, temp_dir):
        """Test verify_schema handles non-existent database."""
        db_path = temp_dir / "nonexistent.db"

        result = verify_schema(db_path)

        assert result is False

    def test_get_schema_version(self, initialized_db):
        """Test get_schema_version function."""
        version = get_schema_version(initialized_db)

        # After initialization, latest schema version (v2) is applied
        assert version == 2

    def test_get_schema_version_uninitialized(self, temp_dir):
        """Test get_schema_version returns 0 for uninitialized database."""
        db_path = temp_dir / "test.db"

        version = get_schema_version(db_path)

        assert version == 0

    def test_schema_version_table_structure(self, initialized_db):
        """Test schema_version table has correct structure."""
        db = DatabaseConnection(initialized_db)

        info = db.get_table_info("schema_version")
        column_names = [col["name"] for col in info]

        assert "version" in column_names
        assert "applied_at" in column_names
        assert "description" in column_names

    def test_bills_table_structure(self, initialized_db):
        """Test bills table has correct structure."""
        db = DatabaseConnection(initialized_db)

        info = db.get_table_info("bills")
        column_names = [col["name"] for col in info]

        required_columns = [
            "id",
            "filename",
            "file_hash",
            "pdf_path",
            "practitioner_name",
            "practitioner_type",
            "bill_date",
            "bill_number",
            "total_amount",
            "currency",
            "processed_at",
            "extraction_status",
            "raw_extraction_json",
            "notes",
        ]

        for column in required_columns:
            assert column in column_names

    def test_filename_unique_constraint(self, initialized_db):
        """Test filename has UNIQUE constraint."""
        db = DatabaseConnection(initialized_db)

        # Insert first bill
        db.execute(
            "INSERT INTO bills (filename, file_hash, pdf_path) VALUES (?, ?, ?)",
            ("test.pdf", "hash1", "/tmp/test.pdf"),
        )

        # Try to insert duplicate filename
        with pytest.raises(DatabaseError):
            db.execute(
                "INSERT INTO bills (filename, file_hash, pdf_path) VALUES (?, ?, ?)",
                ("test.pdf", "hash2", "/tmp/test2.pdf"),
            )
