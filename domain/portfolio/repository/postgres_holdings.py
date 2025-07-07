
"""PostgreSQL unified holdings repository - wrapper around equity and cash holdings repositories."""

from domain.portfolio.repository.base import HoldingRepository, EquityHoldingRepository, CashHoldingRepository
from domain.portfolio.repository.postgres_equity_holdings import PostgresEquityHoldingRepository
from domain.portfolio.repository.postgres_cash_holdings import PostgresCashHoldingRepository
from typing import List, Optional
from uuid import UUID
from domain.portfolio.models.holding import CashHolding, EquityHolding


class PostgresHoldingRepository(HoldingRepository):
    """Unified repository that wraps separate equity and cash holding repositories."""
    
    def __init__(self, db):
        self.db = db
        self.equity_holding_repo: EquityHoldingRepository = PostgresEquityHoldingRepository(db)
        self.cash_holding_repo: CashHoldingRepository = PostgresCashHoldingRepository(db)

    def find_equity_holdings_by_portfolio_id(self, portfolio_id: UUID, *, limit: int = 100, offset: int = 0, conn=None) -> List[EquityHolding]:
        """Find all equity holdings for a portfolio."""
        return self.equity_holding_repo.find_by_portfolio_id(portfolio_id, limit=limit, offset=offset, conn=conn)

    def find_cash_holdings_by_portfolio_id(self, portfolio_id: UUID, *, limit: int = 100, offset: int = 0, conn=None) -> List[CashHolding]:
        """Find all cash holdings for a portfolio."""
        return self.cash_holding_repo.find_by_portfolio_id(portfolio_id, limit=limit, offset=offset, conn=conn)

    def get_equity_holding(self, holding_id: UUID, conn=None) -> Optional[EquityHolding]:
        """Get an equity holding by ID."""
        return self.equity_holding_repo.get(holding_id, conn=conn)

    def get_cash_holding(self, holding_id: UUID, conn=None) -> Optional[CashHolding]:
        """Get a cash holding by ID."""
        return self.cash_holding_repo.get(holding_id, conn=conn)

    def find_equity_by_portfolio_and_stock(self, portfolio_id: UUID, stock_id: UUID, conn=None) -> Optional[EquityHolding]:
        """Find an equity holding by portfolio and stock ID."""
        return self.equity_holding_repo.find_by_portfolio_and_equity(portfolio_id, stock_id, conn=conn)

    def find_cash_by_portfolio_and_currency(self, portfolio_id: UUID, currency: str, conn=None) -> Optional[CashHolding]:
        """Find a cash holding by portfolio and currency."""
        return self.cash_holding_repo.find_by_portfolio_and_currency(portfolio_id, currency, conn=conn)

    def save_equity_holding(self, holding: EquityHolding, conn=None) -> None:
        """Save an equity holding."""
        self.equity_holding_repo.save(holding, conn=conn)

    def save_cash_holding(self, holding: CashHolding, conn=None) -> None:
        """Save a cash holding."""
        self.cash_holding_repo.save(holding, conn=conn)

    def delete_equity_holding(self, holding_id: UUID, conn=None) -> None:
        """Delete an equity holding."""
        self.equity_holding_repo.delete(holding_id, conn=conn)

    def delete_cash_holding(self, holding_id: UUID, conn=None) -> None:
        """Delete a cash holding."""
        self.cash_holding_repo.delete(holding_id, conn=conn)

    def batch_save_equity_holdings(self, holdings: List[EquityHolding], conn=None) -> None:
        """Save multiple equity holdings."""
        self.equity_holding_repo.batch_save(holdings, conn=conn)

    def batch_save_cash_holdings(self, holdings: List[CashHolding], conn=None) -> None:
        """Save multiple cash holdings."""
        self.cash_holding_repo.batch_save(holdings, conn=conn)

    # Legacy methods for backward compatibility (deprecated)
    def find_by_portfolio_id(self, portfolio_id: UUID, *, limit: int = 100, offset: int = 0, conn=None) -> List[EquityHolding]:
        """Legacy method - use find_equity_holdings_by_portfolio_id instead."""
        return self.find_equity_holdings_by_portfolio_id(portfolio_id, limit=limit, offset=offset, conn=conn)

    def get(self, holding_id: UUID, conn=None) -> Optional[EquityHolding]:
        """Legacy method - use get_equity_holding instead."""
        return self.get_equity_holding(holding_id, conn=conn)

    def find_by_portfolio_and_stock(self, portfolio_id: UUID, stock_id: UUID, conn=None) -> Optional[EquityHolding]:
        """Legacy method - use find_equity_by_portfolio_and_stock instead."""
        return self.find_equity_by_portfolio_and_stock(portfolio_id, stock_id, conn=conn)

    def save(self, holding: EquityHolding, conn=None) -> None:
        """Legacy method - use save_equity_holding instead."""
        self.save_equity_holding(holding, conn=conn)

    def delete(self, holding_id: UUID, conn=None) -> None:
        """Legacy method - use delete_equity_holding instead."""
        self.delete_equity_holding(holding_id, conn=conn)

    def batch_save(self, holdings: List[EquityHolding], conn=None) -> None:
        """Legacy method - use batch_save_equity_holdings instead."""
        self.batch_save_equity_holdings(holdings, conn=conn)