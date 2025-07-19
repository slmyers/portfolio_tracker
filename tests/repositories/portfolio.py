"""Test-specific in-memory portfolio repository with mocking and assertion utilities."""

from typing import Optional, List, Dict
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from domain.portfolio.models.portfolio import Portfolio, PortfolioName


class InMemoryPortfolioRepository:
    """Test-specific in-memory implementation of PortfolioRepository with utilities for testing."""
    
    def __init__(self, cash_holding_repo=None):
        self._portfolios: Dict[UUID, dict] = {}
        self._cash_holding_repo = cash_holding_repo
        self._call_history: List[dict] = []

    def get(self, portfolio_id: UUID, conn=None) -> Optional[Portfolio]:
        self._record_call('get', {'portfolio_id': portfolio_id})
        row = self._portfolios.get(portfolio_id)
        if not row:
            return None
        portfolio = self._row_to_portfolio(row)
        
        # Calculate cash balance from cash holdings
        self._add_cash_balance(portfolio)
        
        return portfolio

    def _add_cash_balance(self, portfolio: Portfolio):
        """Add cash_balance property calculated from cash holdings."""
        if self._cash_holding_repo:
            cash_holdings = self._cash_holding_repo.find_by_portfolio_id(portfolio.id)
            usd_cash = Decimal('0')
            for holding in cash_holdings:
                if hasattr(holding.currency, 'value') and holding.currency.value == 'USD':
                    usd_cash += holding.balance
                elif str(holding.currency) == 'USD':
                    usd_cash += holding.balance
            portfolio.cash_balance = usd_cash
        else:
            portfolio.cash_balance = Decimal('0')

    def find_by_tenant_id(self, tenant_id: UUID, conn=None) -> List[Portfolio]:
        self._record_call('find_by_tenant_id', {'tenant_id': tenant_id})
        portfolios = [
            self._row_to_portfolio(row) 
            for row in self._portfolios.values() 
            if row['tenant_id'] == tenant_id
        ]
        
        # Add cash_balance to each portfolio
        for portfolio in portfolios:
            self._add_cash_balance(portfolio)
        
        return portfolios

    def find_by_name(self, tenant_id: UUID, name: str, conn=None) -> Optional[Portfolio]:
        self._record_call('find_by_name', {'tenant_id': tenant_id, 'name': name})
        for row in self._portfolios.values():
            if row['tenant_id'] == tenant_id and row['name'] == name:
                portfolio = self._row_to_portfolio(row)
                self._add_cash_balance(portfolio)
                return portfolio
        return None

    def save(self, portfolio: Portfolio, conn=None) -> None:
        self._record_call('save', {'portfolio_id': portfolio.id})
        self._portfolios[portfolio.id] = self._portfolio_to_row(portfolio)

    def delete(self, portfolio_id: UUID, conn=None) -> None:
        self._record_call('delete', {'portfolio_id': portfolio_id})
        self._portfolios.pop(portfolio_id, None)

    def exists(self, portfolio_id: UUID, conn=None) -> bool:
        self._record_call('exists', {'portfolio_id': portfolio_id})
        return portfolio_id in self._portfolios

    def _portfolio_to_row(self, portfolio: Portfolio) -> dict:
        return {
            'id': portfolio.id,
            'tenant_id': portfolio.tenant_id,
            'name': str(portfolio.name),
            'created_at': portfolio.created_at,
            'updated_at': portfolio.updated_at,
        }

    def _row_to_portfolio(self, row: dict) -> Portfolio:
        """Create a Portfolio object without triggering events."""
        portfolio = Portfolio.__new__(Portfolio)
        portfolio._events = []  # Initialize the events list
        portfolio.id = row['id']
        portfolio.tenant_id = row['tenant_id']
        portfolio.name = PortfolioName(row['name'])
        portfolio.created_at = row['created_at']
        portfolio.updated_at = row['updated_at']
        return portfolio

    def _record_call(self, method: str, args: dict):
        """Record method calls for testing assertions."""
        self._call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now()
        })

    # Test utility methods
    def mock_portfolio(
        self, 
        portfolio_id: UUID = None, 
        tenant_id: UUID = None, 
        name: str = "Test Portfolio",
        created_at: datetime = None,
        updated_at: datetime = None
    ) -> Portfolio:
        """Create and save a mock portfolio for testing."""
        portfolio_id = portfolio_id or uuid4()
        tenant_id = tenant_id or uuid4()
        created_at = created_at or datetime.now()
        updated_at = updated_at or datetime.now()
        
        portfolio = Portfolio(
            id=portfolio_id,
            tenant_id=tenant_id,
            name=PortfolioName(name)
        )
        portfolio.created_at = created_at
        portfolio.updated_at = updated_at
        
        self.save(portfolio)
        return portfolio

    def assert_portfolio_exists(self, portfolio_id: UUID) -> bool:
        """Assert that a portfolio exists in the repository."""
        return self.exists(portfolio_id)

    def assert_portfolio_count_for_tenant(self, tenant_id: UUID, expected_count: int) -> bool:
        """Assert the number of portfolios for a tenant."""
        portfolios = self.find_by_tenant_id(tenant_id)
        return len(portfolios) == expected_count

    def assert_method_called(self, method_name: str, times: int = None) -> bool:
        """Assert that a method was called a specific number of times."""
        calls = [call for call in self._call_history if call['method'] == method_name]
        if times is None:
            return len(calls) > 0
        return len(calls) == times

    def get_call_history(self) -> List[dict]:
        """Get the history of method calls for testing."""
        return self._call_history

    def clear_call_history(self):
        """Clear the call history for testing."""
        self._call_history = []

    def clear_data(self):
        """Clear all portfolio data for testing."""
        self._portfolios.clear()
        self.clear_call_history()

    def get_portfolio_count(self) -> int:
        """Get the total number of portfolios in the repository."""
        return len(self._portfolios)
