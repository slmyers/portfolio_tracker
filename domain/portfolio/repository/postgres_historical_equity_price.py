"""PostgreSQL repository implementation for historical equity prices."""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from domain.portfolio.models.historical_equity_price import HistoricalEquityPrice

class PostgresHistoricalEquityPriceRepository:
    """PostgreSQL implementation of HistoricalEquityPriceRepository."""

    def __init__(self, db):
        self.db = db

    def _row_to_historical_equity_price(self, row) -> HistoricalEquityPrice:
        """Convert database row to HistoricalEquityPrice object."""
        return HistoricalEquityPrice(
            id=UUID(row["id"]),
            equity_id=UUID(row["equity_id"]),
            price=Decimal(str(row["price"])),
            recorded_at=row["recorded_at"]
        )

    def find_by_equity_id(self, equity_id: UUID, *, start_date: datetime, end_date: datetime, conn=None) -> List[HistoricalEquityPrice]:
        """Find historical equity prices by equity ID within a date range."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT * FROM historical_equity_price
                    WHERE equity_id = %s AND recorded_at BETWEEN %s AND %s
                    ORDER BY recorded_at
                    """,
                    (str(equity_id), start_date, end_date)
                )
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_historical_equity_price(dict(zip(colnames, row))) for row in rows]
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def save(self, price_record: HistoricalEquityPrice, conn=None) -> None:
        """Save a historical equity price record."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO historical_equity_price (id, equity_id, price, recorded_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id, recorded_at) DO UPDATE SET
                        price = EXCLUDED.price
                    """,
                    (
                        str(price_record.id),
                        str(price_record.equity_id),
                        price_record.price,
                        price_record.recorded_at
                    )
                )
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def batch_save(self, price_records: List[HistoricalEquityPrice], conn=None) -> None:
        """Save multiple historical equity price records."""
        for price_record in price_records:
            self.save(price_record, conn)

    def delete(self, id: UUID, recorded_at: datetime, conn=None) -> None:
        """Delete a historical equity price record by ID and recorded_at."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM historical_equity_price WHERE id = %s AND recorded_at = %s
                    """,
                    (str(id), recorded_at)
                )
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)
