"""PostgreSQL repository implementation for Activity Report Entry."""

import json
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from ..models.activity_report_entry import ActivityReportEntry
from ..models.enums import Currency
from .base import ActivityReportEntryRepository

class PostgresActivityReportEntryRepository(ActivityReportEntryRepository):
    def __init__(self, db):
        self.db = db

    def _hydrate_entry(self, id: UUID, portfolio_id: UUID, equity_id: Optional[UUID],
                      activity_type: str, amount: Decimal, currency: Currency, date: datetime,
                      raw_data: dict, created_at: datetime) -> ActivityReportEntry:
        """Create an ActivityReportEntry object without triggering events."""
        entry = ActivityReportEntry.__new__(ActivityReportEntry)
        entry._events = []  # Initialize the events list
        entry.id = id
        entry.portfolio_id = portfolio_id
        entry.equity_id = equity_id
        entry.activity_type = activity_type
        entry.amount = amount
        entry.currency = currency
        entry.date = date
        entry.raw_data = raw_data
        entry.created_at = created_at
        return entry

    def _row_to_entry(self, row) -> ActivityReportEntry:
        # Deserialize raw_data if it's a JSON string
        raw_data = row["raw_data"]
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except (json.JSONDecodeError, TypeError):
                raw_data = {}
        elif raw_data is None:
            raw_data = {}
            
        return self._hydrate_entry(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            portfolio_id=UUID(row["portfolio_id"]) if not isinstance(row["portfolio_id"], UUID) else row["portfolio_id"],
            equity_id=UUID(row["equity_id"]) if row["equity_id"] and not isinstance(row["equity_id"], UUID) else row["equity_id"],
            activity_type=row["activity_type"],
            amount=Decimal(str(row["amount"])),
            currency=Currency(row["currency"]),
            date=row["date"],
            raw_data=raw_data,
            created_at=row["created_at"]
        )

    def find_by_portfolio_id(self, portfolio_id: UUID, *, limit: int = 100, offset: int = 0, 
                           activity_type: Optional[str] = None, conn=None) -> List[ActivityReportEntry]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                if activity_type:
                    cur.execute("""
                        SELECT * FROM activity_report_entry 
                        WHERE portfolio_id = %s AND activity_type = %s
                        ORDER BY date DESC 
                        LIMIT %s OFFSET %s
                    """, (str(portfolio_id), activity_type, limit, offset))
                else:
                    cur.execute("""
                        SELECT * FROM activity_report_entry 
                        WHERE portfolio_id = %s 
                        ORDER BY date DESC 
                        LIMIT %s OFFSET %s
                    """, (str(portfolio_id), limit, offset))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_entry(dict(zip(colnames, row))) for row in rows]
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def get(self, entry_id: UUID, conn=None) -> Optional[ActivityReportEntry]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM activity_report_entry WHERE id = %s
                """, (str(entry_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_entry(dict(zip(colnames, row)))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def save(self, entry: ActivityReportEntry, conn=None) -> None:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                # Serialize raw_data to JSON string - always serialize, even if empty dict
                raw_data_json = json.dumps(entry.raw_data if entry.raw_data is not None else {})
                
                cur.execute("""
                    INSERT INTO activity_report_entry 
                    (id, portfolio_id, equity_id, activity_type, amount, currency, date, raw_data, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id, date, portfolio_id) DO UPDATE SET
                        activity_type = EXCLUDED.activity_type,
                        amount = EXCLUDED.amount,
                        currency = EXCLUDED.currency,
                        raw_data = EXCLUDED.raw_data
                """, (
                    str(entry.id),
                    str(entry.portfolio_id),
                    str(entry.equity_id) if entry.equity_id else None,
                    entry.activity_type,
                    entry.amount,
                    entry.currency.value if hasattr(entry.currency, 'value') else entry.currency,
                    entry.date,
                    raw_data_json,
                    entry.created_at
                ))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def delete(self, entry_id: UUID, conn=None) -> None:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM activity_report_entry WHERE id = %s
                """, (str(entry_id),))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def batch_save(self, entries: List[ActivityReportEntry], conn=None) -> None:
        """Save multiple activity report entries."""
        for entry in entries:
            self.save(entry, conn)

    def exists(self, entry_id: UUID, conn=None) -> bool:
        """Check if an activity report entry exists."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM activity_report_entry WHERE id = %s
                """, (str(entry_id),))
                return cur.fetchone() is not None
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def find_by_date_range(self, portfolio_id: UUID, start_date: str, end_date: str, conn=None) -> List[ActivityReportEntry]:
        """Find activity report entries within a date range."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM activity_report_entry 
                    WHERE portfolio_id = %s AND date BETWEEN %s AND %s
                    ORDER BY date DESC
                """, (str(portfolio_id), start_date, end_date))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_entry(dict(zip(colnames, row))) for row in rows]
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)
