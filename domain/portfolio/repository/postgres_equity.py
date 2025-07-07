"""PostgreSQL repository implementation for Equity entities."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from domain.portfolio.repository.base import EquityRepository
from domain.portfolio.models.holding import Equity
from domain.portfolio.models.enums import Exchange


class PostgresEquityRepository(EquityRepository):
    """PostgreSQL implementation of EquityRepository."""
    
    def __init__(self, db):
        self.db = db

    def _hydrate_equity(self, id: UUID, symbol: str, name: Optional[str],
                       exchange: Optional[str], created_at: datetime) -> Equity:
        """Create an Equity object without triggering events."""
        equity = Equity.__new__(Equity)
        equity._events = []  # Initialize the events list
        equity.id = id
        equity.symbol = symbol
        equity.name = name
        equity.exchange = Exchange(exchange) if exchange else None
        equity.created_at = created_at
        return equity

    def _row_to_equity(self, row) -> Equity:
        """Convert database row to Equity object."""
        return self._hydrate_equity(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            symbol=row["symbol"],
            name=row["name"],
            exchange=row["exchange"],
            created_at=row["created_at"]
        )

    def get(self, equity_id: UUID, conn=None) -> Optional[Equity]:
        """Get an equity by ID."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM equity WHERE id = %s
                """, (str(equity_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_equity(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def find_by_symbol(self, symbol: str, exchange: str, conn=None) -> Optional[Equity]:
        """Find an equity by symbol and exchange."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM equity WHERE symbol = %s AND exchange = %s
                """, (symbol, exchange))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_equity(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def find_by_portfolio_id(self, portfolio_id: UUID, conn=None) -> List[Equity]:
        """Find all equities associated with a portfolio."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT e.* FROM equity e
                    JOIN equity_holding eh ON e.id = eh.equity_id
                    WHERE eh.portfolio_id = %s
                """, (str(portfolio_id),))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_equity(dict(zip(colnames, row))) for row in rows]
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def search(self, query: str, limit: int = 50, conn=None) -> List[Equity]:
        """Search for equities by symbol or name."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM equity 
                    WHERE symbol ILIKE %s OR name ILIKE %s
                    ORDER BY symbol
                    LIMIT %s
                """, (f"%{query}%", f"%{query}%", limit))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_equity(dict(zip(colnames, row))) for row in rows]
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def save(self, equity: Equity, conn=None) -> None:
        """Save an equity."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                # Check if equity already exists
                cur.execute("""
                    SELECT id FROM equity WHERE id = %s
                """, (str(equity.id),))
                
                if cur.fetchone():
                    # Update existing equity
                    cur.execute("""
                        UPDATE equity SET symbol = %s, name = %s, exchange = %s
                        WHERE id = %s
                    """, (
                        equity.symbol,
                        equity.name,
                        equity.exchange.value if hasattr(equity.exchange, 'value') else equity.exchange,
                        str(equity.id)
                    ))
                else:
                    # Insert new equity
                    cur.execute("""
                        INSERT INTO equity (id, symbol, name, exchange, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        str(equity.id),
                        equity.symbol,
                        equity.name,
                        equity.exchange.value if hasattr(equity.exchange, 'value') else equity.exchange,
                        equity.created_at
                    ))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def delete(self, equity_id: UUID, conn=None) -> None:
        """Delete an equity."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM equity WHERE id = %s
                """, (str(equity_id),))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def exists(self, equity_id: UUID, conn=None) -> bool:
        """Check if an equity exists."""
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM equity WHERE id = %s
                """, (str(equity_id),))
                return cur.fetchone() is not None
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)