"""Repository for bill database operations."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from ...core.exceptions import DatabaseError, DuplicateBillError
from ...utils.logger import get_logger
from ..models import Bill, BillCreate, BillFilter, BillUpdate
from .base import BaseRepository

logger = get_logger(__name__)


class BillRepository(BaseRepository[Bill]):
    """Repository for managing bill data."""

    def __init__(self, db_path: Path):
        """
        Initialize bill repository.

        Args:
            db_path: Path to SQLite database
        """
        super().__init__(db_path, Bill)

    def create(self, bill: BillCreate) -> Bill:
        """
        Create a new bill record.

        Args:
            bill: Bill data to create

        Returns:
            Created bill with database ID

        Raises:
            DuplicateBillError: If file hash or filename already exists
            DatabaseError: If creation fails
        """
        # Check for duplicate file hash
        if self.check_duplicate_hash(bill.file_hash):
            raise DuplicateBillError(
                f"Bill with file hash {bill.file_hash} already exists"
            )

        # Check for duplicate filename
        if self.get_by_filename(bill.filename) is not None:
            raise DuplicateBillError(
                f"Bill with filename '{bill.filename}' already exists"
            )

        sql = """
            INSERT INTO bills (
                filename, file_hash, pdf_path,
                practitioner_name, practitioner_type,
                bill_date, bill_number, total_amount, currency,
                extraction_status, raw_extraction_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                sql,
                (
                    bill.filename,
                    bill.file_hash,
                    bill.pdf_path,
                    bill.practitioner_name,
                    bill.practitioner_type,
                    bill.bill_date,
                    bill.bill_number,
                    bill.total_amount,
                    bill.currency,
                    bill.extraction_status,
                    bill.raw_extraction_json,
                    bill.notes,
                ),
            )
            bill_id = cursor.lastrowid

        logger.info(f"Created bill with ID {bill_id}: {bill.filename}")
        return self.get_by_id(bill_id)

    def get_by_id(self, bill_id: int) -> Optional[Bill]:
        """
        Get bill by ID.

        Args:
            bill_id: Bill ID

        Returns:
            Bill if found, None otherwise
        """
        sql = "SELECT * FROM bills WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (bill_id,))
            row = cursor.fetchone()

        if row is None:
            return None

        return Bill(**self._row_to_dict(row))

    def get_by_filename(self, filename: str) -> Optional[Bill]:
        """
        Get bill by filename.

        Args:
            filename: PDF filename

        Returns:
            Bill if found, None otherwise
        """
        sql = "SELECT * FROM bills WHERE filename = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (filename,))
            row = cursor.fetchone()

        if row is None:
            return None

        return Bill(**self._row_to_dict(row))

    def check_duplicate_hash(self, file_hash: str) -> bool:
        """
        Check if a bill with the given file hash already exists.

        Args:
            file_hash: SHA256 file hash

        Returns:
            True if duplicate exists, False otherwise
        """
        sql = "SELECT COUNT(*) FROM bills WHERE file_hash = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (file_hash,))
            count = cursor.fetchone()[0]

        return count > 0

    def get_all(self, limit: Optional[int] = None) -> List[Bill]:
        """
        Get all bills.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of bills ordered by bill_date descending
        """
        sql = "SELECT * FROM bills ORDER BY bill_date DESC"
        if limit:
            sql += f" LIMIT {limit}"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchall()

        return [Bill(**self._row_to_dict(row)) for row in rows]

    def get_by_date_range(self, start_date: date, end_date: date) -> List[Bill]:
        """
        Get bills within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of bills in date range
        """
        sql = """
            SELECT * FROM bills
            WHERE bill_date >= ? AND bill_date <= ?
            ORDER BY bill_date DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (start_date, end_date))
            rows = cursor.fetchall()

        return [Bill(**self._row_to_dict(row)) for row in rows]

    def get_by_year(self, year: int) -> List[Bill]:
        """
        Get bills for a specific year.

        Args:
            year: Year (e.g., 2024)

        Returns:
            List of bills for that year
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        return self.get_by_date_range(start_date, end_date)

    def get_by_status(self, status: str) -> List[Bill]:
        """
        Get bills by extraction status.

        Args:
            status: Extraction status (success, failed, needs_review)

        Returns:
            List of bills with that status
        """
        sql = """
            SELECT * FROM bills
            WHERE extraction_status = ?
            ORDER BY bill_date DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (status,))
            rows = cursor.fetchall()

        return [Bill(**self._row_to_dict(row)) for row in rows]

    def filter(self, filter_criteria: BillFilter) -> List[Bill]:
        """
        Filter bills by multiple criteria.

        Args:
            filter_criteria: Filter criteria

        Returns:
            List of bills matching criteria
        """
        conditions = []
        params = []

        # Year filter
        if filter_criteria.year:
            start_date = date(filter_criteria.year, 1, 1)
            end_date = date(filter_criteria.year, 12, 31)
            conditions.append("bill_date >= ? AND bill_date <= ?")
            params.extend([start_date, end_date])

        # Date range filter
        if filter_criteria.start_date:
            conditions.append("bill_date >= ?")
            params.append(filter_criteria.start_date)

        if filter_criteria.end_date:
            conditions.append("bill_date <= ?")
            params.append(filter_criteria.end_date)

        # Practitioner filters
        if filter_criteria.practitioner_name:
            conditions.append("practitioner_name LIKE ?")
            params.append(f"%{filter_criteria.practitioner_name}%")

        if filter_criteria.practitioner_type:
            conditions.append("practitioner_type = ?")
            params.append(filter_criteria.practitioner_type)

        # Status filter
        if filter_criteria.extraction_status:
            conditions.append("extraction_status = ?")
            params.append(filter_criteria.extraction_status)

        # Amount filters
        if filter_criteria.min_amount is not None:
            conditions.append("total_amount >= ?")
            params.append(filter_criteria.min_amount)

        if filter_criteria.max_amount is not None:
            conditions.append("total_amount <= ?")
            params.append(filter_criteria.max_amount)

        # Build query
        sql = "SELECT * FROM bills"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY bill_date DESC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, tuple(params))
            rows = cursor.fetchall()

        return [Bill(**self._row_to_dict(row)) for row in rows]

    def update(self, bill_id: int, updates: BillUpdate) -> Bill:
        """
        Update bill fields.

        Args:
            bill_id: Bill ID to update
            updates: Fields to update

        Returns:
            Updated bill

        Raises:
            DatabaseError: If bill not found or update fails
        """
        # Get current bill to verify it exists
        bill = self.get_by_id(bill_id)
        if bill is None:
            raise DatabaseError(f"Bill with ID {bill_id} not found")

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        for field, value in updates.model_dump(exclude_none=True).items():
            update_fields.append(f"{field} = ?")
            params.append(value)

        if not update_fields:
            # No fields to update
            return bill

        params.append(bill_id)  # Add ID for WHERE clause

        sql = f"UPDATE bills SET {', '.join(update_fields)} WHERE id = ?"

        with self.db.get_connection() as conn:
            conn.execute(sql, tuple(params))

        logger.info(f"Updated bill {bill_id}")
        return self.get_by_id(bill_id)

    def delete(self, bill_id: int) -> bool:
        """
        Delete a bill.

        Args:
            bill_id: Bill ID to delete

        Returns:
            True if deleted, False if not found
        """
        sql = "DELETE FROM bills WHERE id = ?"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, (bill_id,))
            deleted = cursor.rowcount > 0

        if deleted:
            logger.info(f"Deleted bill {bill_id}")

        return deleted

    def get_total_amount(
        self,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Decimal:
        """
        Calculate total amount of bills.

        Args:
            year: Optional year filter
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Total amount as Decimal
        """
        conditions = []
        params = []

        if year:
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            conditions.append("bill_date >= ? AND bill_date <= ?")
            params.extend([start, end])

        if start_date:
            conditions.append("bill_date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("bill_date <= ?")
            params.append(end_date)

        sql = "SELECT COALESCE(SUM(total_amount), 0) FROM bills"
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql, tuple(params))
            total = cursor.fetchone()[0]

        return Decimal(str(total))

    def count(self, filter_criteria: Optional[BillFilter] = None) -> int:
        """
        Count bills matching criteria.

        Args:
            filter_criteria: Optional filter criteria

        Returns:
            Count of matching bills
        """
        if filter_criteria:
            bills = self.filter(filter_criteria)
            return len(bills)

        sql = "SELECT COUNT(*) FROM bills"

        with self.db.get_connection() as conn:
            cursor = conn.execute(sql)
            count = cursor.fetchone()[0]

        return count
