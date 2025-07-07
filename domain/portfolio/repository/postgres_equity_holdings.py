"""PostgreSQL repository implementation for equity holdings."""

from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from domain.portfolio.repository.base import EquityHoldingRepository
from domain.portfolio.models.holding import EquityHolding


class PostgresEquityHoldingRepository(EquityHoldingRepository):
    """PostgreSQL implementation of EquityHoldingRepository."""
    
    def __init__(self, db):
        self.db = db

    def _hydrate_equity_holding(self, id: UUID, portfolio_id: UUID, equity_id: UUID,
                               quantity: Decimal, cost_basis: Decimal, current_value: Decimal,
                               created_at: datetime, updated_at: datetime) -> EquityHolding:
        """Create an EquityHolding object without triggering events."""
        holding = EquityHolding.__new__(EquityHolding)
        holding._events = []  # Initialize the events list
        holding.id = id
        holding.portfolio_id = portfolio_id
        holding.equity_id = equity_id
        holding.quantity = quantity
        holding.cost_basis = cost_basis
        holding.current_value = current_value
        holding.created_at = created_at
        holding.updated_at = updated_at
        return holding

    def _row_to_equity_holding(self, row) -> EquityHolding:
        """Convert database row to EquityHolding object."""
        return self._hydrate_equity_holding(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            portfolio_id=UUID(row["portfolio_id"]) if not isinstance(row["portfolio_id"], UUID) else row["portfolio_id"],
            equity_id=UUID(row["equity_id"]) if not isinstance(row["equity_id"], UUID) else row["equity_id"],
            quantity=Decimal(str(row["quantity"])),
            cost_basis=Decimal(str(row["cost_basis"])),
            current_value=Decimal(str(row["current_value"])),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def find_by_portfolio_id(self, portfolio_id: UUID, *, limit: int = 100, offset: int = 0, conn=None) -> List[EquityHolding]:
        """Find all equity holdings for a portfolio."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM equity_holding 
                    WHERE portfolio_id = %s 
                    ORDER BY created_at 
                    LIMIT %s OFFSET %s
                """, (str(portfolio_id), limit, offset))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_equity_holding(dict(zip(colnames, row))) for row in rows]
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def get(self, holding_id: UUID, conn=None) -> Optional[EquityHolding]:
        """Get an equity holding by ID."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM equity_holding WHERE id = %s
                """, (str(holding_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_equity_holding(dict(zip(colnames, row)))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def find_by_portfolio_and_equity(self, portfolio_id: UUID, equity_id: UUID, conn=None) -> Optional[EquityHolding]:
        """Find an equity holding by portfolio and equity ID."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM equity_holding 
                    WHERE portfolio_id = %s AND equity_id = %s
                """, (str(portfolio_id), str(equity_id)))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_equity_holding(dict(zip(colnames, row)))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def save(self, holding: EquityHolding, conn=None) -> None:
        """Save an equity holding."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO equity_holding (id, portfolio_id, equity_id, quantity, cost_basis, current_value, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        cost_basis = EXCLUDED.cost_basis,
                        current_value = EXCLUDED.current_value,
                        updated_at = EXCLUDED.updated_at
                """, (
                    str(holding.id),
                    str(holding.portfolio_id),
                    str(holding.equity_id),
                    holding.quantity,
                    holding.cost_basis,
                    holding.current_value,
                    holding.created_at,
                    holding.updated_at
                ))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def delete(self, holding_id: UUID, conn=None) -> None:
        """Delete an equity holding."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM equity_holding WHERE id = %s
                """, (str(holding_id),))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def batch_save(self, holdings: List[EquityHolding], conn=None) -> None:
        """Save multiple equity holdings."""
        for holding in holdings:
            self.save(holding, conn)

    def exists(self, holding_id: UUID, conn=None) -> bool:
        """Check if an equity holding exists."""
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM equity_holding WHERE id = %s
                """, (str(holding_id),))
                return cur.fetchone() is not None
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)
