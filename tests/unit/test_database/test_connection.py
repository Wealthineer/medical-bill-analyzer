"""Tests for database connection management."""

from decimal import Decimal
from pathlib import Path

import pytest

from medical_bill_analyzer.core.exceptions import DatabaseError
from medical_bill_analyzer.database.connection import DatabaseConnection


class TestDatabaseConnection:
    """Test DatabaseConnection class."""

    def test_init_creates_directory(self, temp_dir):
        """Test that __init__ creates database directory."""
        db_path = temp_dir / "subdir" / "test.db"
        db = DatabaseConnection(db_path)

        assert db.db_path == db_path
        assert db_path.parent.exists()

    def test_get_connection_context_manager(self, test_db_path):
        """Test connection context manager."""
        db = DatabaseConnection(test_db_path)

        with db.get_connection() as conn:
            assert conn is not None
            # Test we can execute queries
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_connection_auto_commit(self, test_db_path):
        """Test connection automatically commits on success."""
        db = DatabaseConnection(test_db_path)

        # Create table and insert data
        with db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, value TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")

        # Verify data persisted
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM test WHERE id = 1")
            result = cursor.fetchone()
            assert result[0] == "test"

    def test_connection_auto_rollback_on_error(self, test_db_path):
        """Test connection automatically rolls back on error."""
        db = DatabaseConnection(test_db_path)

        # Create table
        with db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")

        # Try to insert with error
        try:
            with db.get_connection() as conn:
                conn.execute("INSERT INTO test VALUES (1)")
                # This will fail (syntax error)
                conn.execute("INVALID SQL")
        except DatabaseError:
            pass

        # Verify rollback - no row should exist
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            assert count == 0

    def test_decimal_type_adapter(self, test_db_path):
        """Test Decimal type is properly stored and retrieved."""
        db = DatabaseConnection(test_db_path)

        with db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, amount DECIMAL(10,2))")
            conn.execute("INSERT INTO test VALUES (?, ?)", (1, Decimal("123.45")))

        # Retrieve and verify type is preserved
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT amount FROM test WHERE id = 1")
            result = cursor.fetchone()
            amount = result[0]

            assert isinstance(amount, Decimal)
            assert amount == Decimal("123.45")

    def test_decimal_precision_preserved(self, test_db_path):
        """Test Decimal precision is preserved."""
        db = DatabaseConnection(test_db_path)

        test_values = [
            Decimal("0.01"),
            Decimal("999.99"),
            Decimal("1234.56"),
            Decimal("0.001"),
        ]

        with db.get_connection() as conn:
            conn.execute("CREATE TABLE test (amount DECIMAL)")
            for i, value in enumerate(test_values):
                conn.execute("INSERT INTO test VALUES (?)", (value,))

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT amount FROM test")
            results = [row[0] for row in cursor.fetchall()]

            for original, retrieved in zip(test_values, results):
                assert retrieved == original
                assert isinstance(retrieved, Decimal)

    def test_foreign_keys_enabled(self, test_db_path):
        """Test foreign key support is enabled."""
        db = DatabaseConnection(test_db_path)

        with db.get_connection() as conn:
            # Create tables with foreign key
            conn.execute(
                "CREATE TABLE parent (id INTEGER PRIMARY KEY)"
            )
            conn.execute(
                """CREATE TABLE child (
                    id INTEGER PRIMARY KEY,
                    parent_id INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES parent(id)
                )"""
            )

            # Insert parent
            conn.execute("INSERT INTO parent VALUES (1)")

        # Try to insert child with invalid parent - should fail
        with pytest.raises(DatabaseError):
            with db.get_connection() as conn:
                conn.execute("INSERT INTO child VALUES (1, 999)")

    def test_row_factory_dict_access(self, test_db_path):
        """Test Row factory allows dict-like access."""
        db = DatabaseConnection(test_db_path)

        with db.get_connection() as conn:
            conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'test')")

        with db.get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM test")
            row = cursor.fetchone()

            # Test dict-like access
            assert row["id"] == 1
            assert row["name"] == "test"

            # Test can convert to dict
            row_dict = dict(row)
            assert row_dict == {"id": 1, "name": "test"}

    def test_execute_method_commits_transaction(self, test_db_path):
        """Test execute method commits changes."""
        db = DatabaseConnection(test_db_path)

        # Create table and insert data using execute
        db.execute("CREATE TABLE test (id INTEGER, value TEXT)")
        db.execute("INSERT INTO test VALUES (?, ?)", (1, "test"))

        # Verify data persisted by querying with context manager
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM test WHERE id = ?", (1,))
            result = cursor.fetchone()
            assert result[0] == "test"

    def test_executemany_method_commits(self, test_db_path):
        """Test executemany method commits changes."""
        db = DatabaseConnection(test_db_path)

        db.execute("CREATE TABLE test (id INTEGER, value TEXT)")

        # Insert multiple rows
        data = [(1, "one"), (2, "two"), (3, "three")]
        db.executemany("INSERT INTO test VALUES (?, ?)", data)

        # Verify all inserted using context manager
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test")
            count = cursor.fetchone()[0]
            assert count == 3

    def test_execute_script_method(self, test_db_path):
        """Test execute_script convenience method."""
        db = DatabaseConnection(test_db_path)

        script = """
            CREATE TABLE test1 (id INTEGER);
            CREATE TABLE test2 (id INTEGER);
            INSERT INTO test1 VALUES (1);
            INSERT INTO test2 VALUES (2);
        """

        db.execute_script(script)

        # Verify both tables created
        assert db.table_exists("test1")
        assert db.table_exists("test2")

    def test_table_exists(self, test_db_path):
        """Test table_exists method."""
        db = DatabaseConnection(test_db_path)

        assert not db.table_exists("nonexistent")

        db.execute("CREATE TABLE test (id INTEGER)")
        assert db.table_exists("test")

    def test_get_table_info(self, test_db_path):
        """Test get_table_info method."""
        db = DatabaseConnection(test_db_path)

        db.execute(
            """CREATE TABLE test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                amount DECIMAL
            )"""
        )

        info = db.get_table_info("test")

        assert len(info) == 3
        column_names = [col["name"] for col in info]
        assert "id" in column_names
        assert "name" in column_names
        assert "amount" in column_names

    def test_database_error_on_invalid_sql(self, test_db_path):
        """Test DatabaseError is raised on invalid SQL."""
        db = DatabaseConnection(test_db_path)

        with pytest.raises(DatabaseError) as exc:
            db.execute("INVALID SQL STATEMENT")

        assert "Database operation failed" in str(exc.value)

    def test_connection_closed_after_context(self, test_db_path):
        """Test connection is properly closed after context manager."""
        db = DatabaseConnection(test_db_path)

        conn_ref = None
        with db.get_connection() as conn:
            conn_ref = conn

        # Connection should be closed
        # Trying to use it should raise an error
        with pytest.raises(Exception):  # ProgrammingError
            conn_ref.execute("SELECT 1")
