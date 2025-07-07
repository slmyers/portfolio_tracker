"""PostgreSQL repository implementation for cash holdings."""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from domain.portfolio.repository.base import CashHoldingRepository
from domain.portfolio.models.holding import CashHolding
from domain.portfolio.models.enums import Currency


class PostgresCashHoldingRepository(CashHoldingRepository):
    """PostgreSQL implementation of CashHoldingRepository."""
    
    def __init__(self, db):
        self.db = db

    def _hydrate_cash_holding(self, id: UUID, portfolio_id: UUID, currency: Currency,
                             balance: Decimal, created_at: datetime, updated_at: datetime) -> CashHolding:
        """Create a CashHolding object without triggering events."""
        holding = CashHolding.__new__(CashHolding)
        holding._events = []  # Initialize the events list
        holding.id = id
        holding.portfolio_id = portfolio_id
        holding.currency = currency
        holding.balance = balance
        holding.created_at = created_at
        holding.updated_at = updated_at
        return holding

    def _row_to_cash_holding(self, row) -> CashHolding:
        """Convert database row to CashHolding object."""
        return self._hydrate_cash_holding(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            portfolio_id=UUID(row["portfolio_id"]) if not isinstance(row["portfolio_id"], UUID) else row["portfolio_id"],
            currency=Currency(row["currency"]) if isinstance(row["currency"], str) else row["currency"],
            balance=Decimal(str(row["balance"])),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def find_by_portfolio_id(self, portfolio_id: UUID, *, limit: int = 100, offset: int = 0, conn=None) -> List[CashHolding]:
        """Find all cash holdings for a portfolio."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM cash_holding 
                    WHERE portfolio_id = %s 
                    ORDER BY created_at 
                    LIMIT %s OFFSET %s
                """, (str(portfolio_id), limit, offset))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_cash_holding(dict(zip(colnames, row))) for row in rows]
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def get(self, holding_id: UUID, conn=None) -> Optional[CashHolding]:
        """Get a cash holding by ID."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM cash_holding WHERE id = %s
                """, (str(holding_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_cash_holding(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def find_by_portfolio_and_currency(self, portfolio_id: UUID, currency: str, conn=None) -> Optional[CashHolding]:
        """Find a cash holding by portfolio and currency."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM cash_holding 
                    WHERE portfolio_id = %s AND currency = %s
                """, (str(portfolio_id), currency))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_cash_holding(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def save(self, cash_holding: CashHolding, conn=None) -> None:
        """Save a cash holding."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO cash_holding (id, portfolio_id, currency, balance, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        balance = EXCLUDED.balance,
                        updated_at = EXCLUDED.updated_at
                """, (
                    str(cash_holding.id),
                    str(cash_holding.portfolio_id),
                    cash_holding.currency.value if hasattr(cash_holding.currency, 'value') else str(cash_holding.currency),
                    cash_holding.balance,
                    cash_holding.created_at,
                    cash_holding.updated_at
                ))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def delete(self, holding_id: UUID, conn=None) -> None:
        """Delete a cash holding."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM cash_holding WHERE id = %s
                """, (str(holding_id),))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def batch_save(self, holdings: List[CashHolding], conn=None) -> None:
        """Save multiple cash holdings."""
        for holding in holdings:
            self.save(holding, conn)

    def exists(self, holding_id: UUID, conn=None) -> bool:
        """Check if a cash holding exists."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM cash_holding WHERE id = %s
                """, (str(holding_id),))
                return cur.fetchone() is not None
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)
