"""Test-specific in-memory equity repository with mocking and assertion utilities."""

from typing import Optional, List, Dict
from uuid import UUID, uuid4
from datetime import datetime

from domain.portfolio.models.holding import Equity


class InMemoryEquityRepository:
    """Test-specific in-memory implementation of EquityRepository with utilities for testing."""
    
    def __init__(self):
        self._equities: Dict[UUID, dict] = {}
        self._call_history: List[dict] = []

    def get(self, equity_id: UUID, conn=None) -> Optional[Equity]:
        self._record_call('get', {'equity_id': equity_id})
        row = self._equities.get(equity_id)
        return self._row_to_equity(row) if row else None

    def find_by_symbol(self, symbol: str, exchange: str, conn=None) -> Optional[Equity]:
        from domain.portfolio.models.enums import Exchange
        self._record_call('find_by_symbol', {'symbol': symbol, 'exchange': exchange})
        
        # Convert string to Exchange enum if needed
        exchange_enum = Exchange(exchange) if isinstance(exchange, str) else exchange
        
        for row in self._equities.values():
            row_exchange = row['exchange']
            # Handle comparison between enum and string
            if (row['symbol'] == symbol and 
                (row_exchange == exchange_enum or 
                 (hasattr(row_exchange, 'value') and row_exchange.value == exchange) or
                 str(row_exchange) == exchange)):
                return self._row_to_equity(row)
        return None

    def find_by_portfolio_id(self, portfolio_id: UUID, conn=None) -> List[Equity]:
        self._record_call('find_by_portfolio_id', {'portfolio_id': portfolio_id})
        # This would require join logic in a real implementation
        # For in-memory, we'll return all equities for simplicity
        return [self._row_to_equity(row) for row in self._equities.values()]

    def search(self, query: str, limit: int = 50, conn=None) -> List[Equity]:
        self._record_call('search', {'query': query, 'limit': limit})
        query_lower = query.lower()
        matches = []
        for row in self._equities.values():
            if (query_lower in row['symbol'].lower() or 
                query_lower in row['name'].lower()):
                matches.append(self._row_to_equity(row))
                if len(matches) >= limit:
                    break
        return matches

    def save(self, equity: Equity, conn=None) -> None:
        self._record_call('save', {'equity_id': equity.id})
        self._equities[equity.id] = self._equity_to_row(equity)

    def delete(self, equity_id: UUID, conn=None) -> None:
        self._record_call('delete', {'equity_id': equity_id})
        self._equities.pop(equity_id, None)

    def exists(self, equity_id: UUID, conn=None) -> bool:
        self._record_call('exists', {'equity_id': equity_id})
        return equity_id in self._equities

    def _equity_to_row(self, equity: Equity) -> dict:
        return {
            'id': equity.id,
            'symbol': equity.symbol,
            'name': equity.name,
            'exchange': equity.exchange,
            'created_at': equity.created_at,
        }

    def _row_to_equity(self, row: dict) -> Equity:
        """Create an Equity object without triggering events."""
        equity = Equity.__new__(Equity)
        equity._events = []  # Initialize the events list
        equity.id = row['id']
        equity.symbol = row['symbol']
        equity.name = row['name']
        equity.exchange = row['exchange']
        equity.created_at = row['created_at']
        return equity

    def _record_call(self, method: str, args: dict):
        """Record method calls for testing assertions."""
        self._call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now()
        })

    # Test utility methods
    def mock_equity(
        self, 
        equity_id: UUID = None, 
        symbol: str = "TEST",
        name: str = "Test Equity",
        exchange = None,
        created_at: datetime = None
    ) -> Equity:
        """Create and save a mock equity for testing."""
        from domain.portfolio.models.enums import Exchange
        
        equity_id = equity_id or uuid4()
        exchange = exchange or Exchange.NASDAQ
        created_at = created_at or datetime.now()
        
        equity = Equity(
            id=equity_id,
            symbol=symbol,
            name=name,
            exchange=exchange
        )
        equity.created_at = created_at
        
        self.save(equity)
        return equity

    def assert_equity_exists(self, equity_id: UUID) -> bool:
        """Assert that an equity exists in the repository."""
        return self.exists(equity_id)

    def assert_equity_count(self, expected_count: int) -> bool:
        """Assert the number of equities in the repository."""
        return len(self._equities) == expected_count

    def assert_method_called(self, method_name: str, times: int = None) -> bool:
        """Assert that a method was called a specific number of times."""
        calls = [call for call in self._call_history if call['method'] == method_name]
        if times is None:
            return len(calls) > 0
        return len(calls) == times

    def assert_equity_by_symbol_exists(self, symbol: str, exchange: str) -> bool:
        """Assert that an equity with given symbol and exchange exists."""
        equity = self.find_by_symbol(symbol, exchange)
        return equity is not None

    def get_call_history(self) -> List[dict]:
        """Get the history of method calls for testing."""
        return self._call_history

    def clear_call_history(self):
        """Clear the call history for testing."""
        self._call_history = []

    def clear_data(self):
        """Clear all equity data for testing."""
        self._equities.clear()
        self.clear_call_history()

    def get_equity_count(self) -> int:
        """Get the total number of equities in the repository."""
        return len(self._equities)
