from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from uuid import UUID
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class PostgresPortfolioRepository:
    """PostgreSQL implementation of PortfolioRepository."""
    
    def __init__(self, db):
        self.db = db

    def _hydrate_portfolio(
        self, 
        id: UUID, 
        tenant_id: UUID, 
        name: PortfolioName, 
        created_at: datetime, 
        updated_at: datetime
    ) -> Portfolio:
        """Create a Portfolio object without triggering events."""
        portfolio = Portfolio.__new__(Portfolio)
        portfolio._events = []  # Initialize the events list
        portfolio.id = id
        portfolio.tenant_id = tenant_id
        portfolio.name = name
        portfolio.created_at = created_at
        portfolio.updated_at = updated_at
        return portfolio

    def _row_to_portfolio(self, row) -> Portfolio:
        return self._hydrate_portfolio(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            tenant_id=UUID(row["tenant_id"]) if not isinstance(row["tenant_id"], UUID) else row["tenant_id"],
            name=PortfolioName(row["name"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get(self, portfolio_id: UUID, conn=None) -> Optional[Portfolio]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM portfolio WHERE id = %s
                """, (str(portfolio_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                portfolio = self._row_to_portfolio(dict(zip(colnames, row)))
                
                # Get cash balance from cash_holding table
                cur.execute("""
                    SELECT COALESCE(SUM(balance), 0) as total_cash 
                    FROM cash_holding 
                    WHERE portfolio_id = %s
                """, (str(portfolio_id),))
                cash_row = cur.fetchone()
                if cash_row:
                    portfolio.cash_balance = Decimal(str(cash_row[0]))
                
                return portfolio
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def find_by_tenant_id(self, tenant_id: UUID, conn=None) -> List[Portfolio]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.*, COALESCE(SUM(ch.balance), 0) as total_cash
                    FROM portfolio p
                    LEFT JOIN cash_holding ch ON p.id = ch.portfolio_id
                    WHERE p.tenant_id = %s
                    GROUP BY p.id, p.tenant_id, p.name, p.created_at, p.updated_at
                """, (str(tenant_id),))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                portfolios = []
                for row in rows:
                    row_dict = dict(zip(colnames, row))
                    portfolio = self._row_to_portfolio(row_dict)
                    portfolio.cash_balance = Decimal(str(row_dict['total_cash']))
                    portfolios.append(portfolio)
                return portfolios
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def save(self, portfolio: Portfolio, conn=None) -> None:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                # Insert or update portfolio
                cur.execute("""
                    INSERT INTO portfolio (id, tenant_id, name, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        updated_at = EXCLUDED.updated_at
                """, (
                    str(portfolio.id),
                    str(portfolio.tenant_id),
                    str(portfolio.name),
                    portfolio.created_at,
                    portfolio.updated_at
                ))
                
                # Update cash balance in cash_holding table only if cash_balance exists
                # For simplicity, we'll use USD as the default currency
                if hasattr(portfolio, 'cash_balance'):
                    cur.execute("""
                        INSERT INTO cash_holding (id, portfolio_id, currency, balance, created_at, updated_at)
                        VALUES (gen_random_uuid(), %s, 'USD', %s, %s, %s)
                        ON CONFLICT (portfolio_id, currency) DO UPDATE SET
                            balance = EXCLUDED.balance,
                            updated_at = EXCLUDED.updated_at
                    """, (
                        str(portfolio.id),
                        portfolio.cash_balance,
                        portfolio.updated_at,
                        portfolio.updated_at
                    ))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def delete(self, portfolio_id: UUID, conn=None) -> None:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                # Delete will cascade to related tables
                cur.execute("""
                    DELETE FROM portfolio WHERE id = %s
                """, (str(portfolio_id),))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def find_by_name(self, tenant_id: UUID, name: str, conn=None) -> Optional[Portfolio]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.*, COALESCE(SUM(ch.balance), 0) as total_cash
                    FROM portfolio p
                    LEFT JOIN cash_holding ch ON p.id = ch.portfolio_id
                    WHERE p.tenant_id = %s AND p.name = %s
                    GROUP BY p.id, p.tenant_id, p.name, p.created_at, p.updated_at
                """, (str(tenant_id), name))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                row_dict = dict(zip(colnames, row))
                portfolio = self._row_to_portfolio(row_dict)
                portfolio.cash_balance = Decimal(str(row_dict['total_cash']))
                return portfolio
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def exists(self, portfolio_id: UUID, conn=None) -> bool:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1 FROM portfolio WHERE id = %s
                """, (str(portfolio_id),))
                return cur.fetchone() is not None
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)