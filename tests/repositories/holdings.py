"""Test-specific in-memory holding repositories with mocking and assertion utilities."""

from typing import Optional, List, Dict
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime

from domain.portfolio.models.holding import EquityHolding, CashHolding
from domain.portfolio.portfolio_errors import DuplicateHoldingError


class InMemoryEquityHoldingRepository:
    """Test-specific in-memory implementation of EquityHoldingRepository with utilities for testing."""
    
    def __init__(self):
        self._holdings: Dict[UUID, dict] = {}
        self._call_history: List[dict] = []

    def find_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        conn=None
    ) -> List[EquityHolding]:
        self._record_call('find_by_portfolio_id', {
            'portfolio_id': portfolio_id, 
            'limit': limit, 
            'offset': offset
        })
        holdings = [
            self._row_to_holding(row) 
            for row in self._holdings.values() 
            if row['portfolio_id'] == portfolio_id
        ]
        return holdings[offset:offset + limit]

    def get(self, holding_id: UUID, conn=None) -> Optional[EquityHolding]:
        self._record_call('get', {'holding_id': holding_id})
        row = self._holdings.get(holding_id)
        return self._row_to_holding(row) if row else None

    def find_by_portfolio_and_equity(
        self, 
        portfolio_id: UUID, 
        equity_id: UUID, 
        conn=None
    ) -> Optional[EquityHolding]:
        self._record_call('find_by_portfolio_and_equity', {
            'portfolio_id': portfolio_id, 
            'equity_id': equity_id
        })
        for row in self._holdings.values():
            if row['portfolio_id'] == portfolio_id and row['equity_id'] == equity_id:
                return self._row_to_holding(row)
        return None

    def save(self, holding: EquityHolding, conn=None) -> None:
        self._record_call('save', {'holding_id': holding.id})
        # Check for duplicate holding for the same equity in the same portfolio
        existing = self.find_by_portfolio_and_equity(
            holding.portfolio_id, holding.equity_id, conn
        )
        if existing and existing.id != holding.id:
            raise DuplicateHoldingError(holding.portfolio_id, holding.equity_id)
        
        self._holdings[holding.id] = self._holding_to_row(holding)

    def delete(self, holding_id: UUID, conn=None) -> None:
        self._record_call('delete', {'holding_id': holding_id})
        self._holdings.pop(holding_id, None)

    def batch_save(self, holdings: List[EquityHolding], conn=None) -> None:
        self._record_call('batch_save', {'count': len(holdings)})
        for holding in holdings:
            self.save(holding, conn)

    def exists(self, holding_id: UUID, conn=None) -> bool:
        self._record_call('exists', {'holding_id': holding_id})
        return holding_id in self._holdings

    def _holding_to_row(self, holding: EquityHolding) -> dict:
        return {
            'id': holding.id,
            'portfolio_id': holding.portfolio_id,
            'equity_id': holding.equity_id,
            'quantity': holding.quantity,
            'cost_basis': holding.cost_basis,
            'current_value': holding.current_value,
            'created_at': holding.created_at,
            'updated_at': holding.updated_at,
        }

    def _row_to_holding(self, row: dict) -> EquityHolding:
        """Create an EquityHolding object without triggering events."""
        holding = EquityHolding.__new__(EquityHolding)
        holding._events = []  # Initialize the events list
        holding.id = row['id']
        holding.portfolio_id = row['portfolio_id']
        holding.equity_id = row['equity_id']
        holding.quantity = row['quantity']
        holding.cost_basis = row['cost_basis']
        holding.current_value = row['current_value']
        holding.created_at = row['created_at']
        holding.updated_at = row['updated_at']
        return holding

    def _record_call(self, method: str, args: dict):
        """Record method calls for testing assertions."""
        self._call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now()
        })

    # Test utility methods
    def mock_equity_holding(
        self, 
        holding_id: UUID = None,
        portfolio_id: UUID = None,
        equity_id: UUID = None,
        quantity: Decimal = Decimal('100'),
        cost_basis: Decimal = Decimal('1000.00'),
        current_value: Decimal = Decimal('1100.00'),
        created_at: datetime = None,
        updated_at: datetime = None
    ) -> EquityHolding:
        """Create and save a mock equity holding for testing."""
        holding_id = holding_id or uuid4()
        portfolio_id = portfolio_id or uuid4()
        equity_id = equity_id or uuid4()
        created_at = created_at or datetime.now()
        updated_at = updated_at or datetime.now()
        
        holding = EquityHolding(
            id=holding_id,
            portfolio_id=portfolio_id,
            equity_id=equity_id,
            quantity=quantity,
            cost_basis=cost_basis,
            current_value=current_value
        )
        holding.created_at = created_at
        holding.updated_at = updated_at
        
        self.save(holding)
        return holding

    def assert_holding_exists(self, holding_id: UUID) -> bool:
        """Assert that a holding exists in the repository."""
        return self.exists(holding_id)

    def assert_holdings_count_for_portfolio(self, portfolio_id: UUID, expected_count: int) -> bool:
        """Assert the number of holdings for a portfolio."""
        holdings = self.find_by_portfolio_id(portfolio_id)
        return len(holdings) == expected_count

    def assert_method_called(self, method_name: str, times: int = None) -> bool:
        """Assert that a method was called a specific number of times."""
        calls = [call for call in self._call_history if call['method'] == method_name]
        if times is None:
            return len(calls) > 0
        return len(calls) == times

    def assert_duplicate_holding_error(self, portfolio_id: UUID, equity_id: UUID) -> bool:
        """Assert that saving a duplicate holding raises DuplicateHoldingError."""
        try:
            duplicate_holding = EquityHolding(
                id=uuid4(),
                portfolio_id=portfolio_id,
                equity_id=equity_id,
                quantity=Decimal('50'),
                cost_basis=Decimal('500.00'),
                current_value=Decimal('550.00')
            )
            self.save(duplicate_holding)
            return False  # Should not reach here
        except DuplicateHoldingError:
            return True

    def get_call_history(self) -> List[dict]:
        """Get the history of method calls for testing."""
        return self._call_history

    def clear_call_history(self):
        """Clear the call history for testing."""
        self._call_history = []

    def clear_data(self):
        """Clear all holding data for testing."""
        self._holdings.clear()
        self.clear_call_history()

    def get_holding_count(self) -> int:
        """Get the total number of holdings in the repository."""
        return len(self._holdings)


class InMemoryCashHoldingRepository:
    """Test-specific in-memory implementation of CashHoldingRepository with utilities for testing."""
    
    def __init__(self):
        self._holdings: Dict[UUID, dict] = {}
        self._call_history: List[dict] = []

    def find_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        conn=None
    ) -> List[CashHolding]:
        self._record_call('find_by_portfolio_id', {
            'portfolio_id': portfolio_id, 
            'limit': limit, 
            'offset': offset
        })
        holdings = [
            self._row_to_cash_holding(row) 
            for row in self._holdings.values() 
            if row['portfolio_id'] == portfolio_id
        ]
        return holdings[offset:offset + limit]

    def get(self, holding_id: UUID, conn=None) -> Optional[CashHolding]:
        self._record_call('get', {'holding_id': holding_id})
        row = self._holdings.get(holding_id)
        return self._row_to_cash_holding(row) if row else None

    def find_by_portfolio_and_currency(
        self, 
        portfolio_id: UUID, 
        currency: str, 
        conn=None
    ) -> Optional[CashHolding]:
        self._record_call('find_by_portfolio_and_currency', {
            'portfolio_id': portfolio_id, 
            'currency': currency
        })
        for row in self._holdings.values():
            # Compare currency values since row['currency'] is a Currency enum
            row_currency = row['currency'].value if hasattr(row['currency'], 'value') else str(row['currency'])
            if row['portfolio_id'] == portfolio_id and row_currency == currency:
                return self._row_to_cash_holding(row)
        return None

    def save(self, cash_holding: CashHolding, conn=None) -> None:
        self._record_call('save', {'holding_id': cash_holding.id})
        self._holdings[cash_holding.id] = self._cash_holding_to_row(cash_holding)

    def delete(self, holding_id: UUID, conn=None) -> None:
        self._record_call('delete', {'holding_id': holding_id})
        self._holdings.pop(holding_id, None)

    def batch_save(self, holdings: List[CashHolding], conn=None) -> None:
        self._record_call('batch_save', {'count': len(holdings)})
        for holding in holdings:
            self.save(holding, conn)

    def exists(self, holding_id: UUID, conn=None) -> bool:
        self._record_call('exists', {'holding_id': holding_id})
        return holding_id in self._holdings

    def _cash_holding_to_row(self, holding: CashHolding) -> dict:
        return {
            'id': holding.id,
            'portfolio_id': holding.portfolio_id,
            'currency': holding.currency,
            'balance': holding.balance,
            'created_at': holding.created_at,
            'updated_at': holding.updated_at,
        }

    def _row_to_cash_holding(self, row: dict) -> CashHolding:
        """Create a CashHolding object without triggering events."""
        holding = CashHolding.__new__(CashHolding)
        holding._events = []  # Initialize the events list
        holding.id = row['id']
        holding.portfolio_id = row['portfolio_id']
        holding.currency = row['currency']
        holding.balance = row['balance']
        holding.created_at = row['created_at']
        holding.updated_at = row['updated_at']
        return holding

    def _record_call(self, method: str, args: dict):
        """Record method calls for testing assertions."""
        self._call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now()
        })

    # Test utility methods
    def mock_cash_holding(
        self, 
        holding_id: UUID = None,
        portfolio_id: UUID = None,
        currency = None,
        balance: Decimal = Decimal('1000.00'),
        created_at: datetime = None,
        updated_at: datetime = None
    ) -> CashHolding:
        """Create and save a mock cash holding for testing."""
        from domain.portfolio.models.enums import Currency
        
        holding_id = holding_id or uuid4()
        portfolio_id = portfolio_id or uuid4()
        currency = currency or Currency.USD
        created_at = created_at or datetime.now()
        updated_at = updated_at or datetime.now()
        
        holding = CashHolding(
            id=holding_id,
            portfolio_id=portfolio_id,
            currency=currency,
            balance=balance
        )
        holding.created_at = created_at
        holding.updated_at = updated_at
        
        self.save(holding)
        return holding

    def assert_holding_exists(self, holding_id: UUID) -> bool:
        """Assert that a cash holding exists in the repository."""
        return self.exists(holding_id)

    def assert_holdings_count_for_portfolio(self, portfolio_id: UUID, expected_count: int) -> bool:
        """Assert the number of cash holdings for a portfolio."""
        holdings = self.find_by_portfolio_id(portfolio_id)
        return len(holdings) == expected_count

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
        """Clear all cash holding data for testing."""
        self._holdings.clear()
        self.clear_call_history()

    def get_holding_count(self) -> int:
        """Get the total number of cash holdings in the repository."""
        return len(self._holdings)
