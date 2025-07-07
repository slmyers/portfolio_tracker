"""In-memory repository implementations for the portfolio domain."""

from typing import Optional, List, Dict
from uuid import UUID

from ..models.portfolio import Portfolio, PortfolioName
from ..models.holding import Equity, EquityHolding, CashHolding
from ..models.activity_report_entry import ActivityReportEntry
from ..portfolio_errors import DuplicateHoldingError


class InMemoryPortfolioRepository:
    """In-memory implementation of PortfolioRepository."""
    
    def __init__(self, cash_holding_repo=None):
        self._portfolios: Dict[UUID, dict] = {}
        self._cash_holding_repo = cash_holding_repo or InMemoryCashHoldingRepository()

    def get(self, portfolio_id: UUID, conn=None) -> Optional[Portfolio]:
        row = self._portfolios.get(portfolio_id)
        if not row:
            return None
        portfolio = self._row_to_portfolio(row)
        
        # Calculate cash balance from cash holdings
        self._add_cash_balance(portfolio)
        
        return portfolio

    def _add_cash_balance(self, portfolio: Portfolio):
        """Add cash_balance property calculated from cash holdings."""
        from decimal import Decimal
        cash_holdings = self._cash_holding_repo.find_by_portfolio_id(portfolio.id)
        usd_cash = Decimal('0')
        for holding in cash_holdings:
            if holding.currency.value == 'USD':  # Only count USD for now
                usd_cash += holding.balance
        portfolio.cash_balance = usd_cash

    def find_by_tenant_id(self, tenant_id: UUID, conn=None) -> List[Portfolio]:
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
        for row in self._portfolios.values():
            if row['tenant_id'] == tenant_id and row['name'] == name:
                portfolio = self._row_to_portfolio(row)
                self._add_cash_balance(portfolio)
                return portfolio
        return None

    def save(self, portfolio: Portfolio, conn=None) -> None:
        self._portfolios[portfolio.id] = self._portfolio_to_row(portfolio)

    def delete(self, portfolio_id: UUID, conn=None) -> None:
        self._portfolios.pop(portfolio_id, None)

    def exists(self, portfolio_id: UUID, conn=None) -> bool:
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


class InMemoryEquityRepository:
    """In-memory implementation of EquityRepository."""
    
    def __init__(self):
        self._equities: Dict[UUID, dict] = {}

    def get(self, equity_id: UUID, conn=None) -> Optional[Equity]:
        row = self._equities.get(equity_id)
        return self._row_to_equity(row) if row else None

    def find_by_symbol(self, symbol: str, exchange: str, conn=None) -> Optional[Equity]:
        from ..models.enums import Exchange
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
        # This would require join logic in a real implementation
        # For in-memory, we'll return all equities for simplicity
        return [self._row_to_equity(row) for row in self._equities.values()]

    def search(self, query: str, limit: int = 50, conn=None) -> List[Equity]:
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
        self._equities[equity.id] = self._equity_to_row(equity)

    def delete(self, equity_id: UUID, conn=None) -> None:
        self._equities.pop(equity_id, None)

    def exists(self, equity_id: UUID, conn=None) -> bool:
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


class InMemoryEquityHoldingRepository:
    """In-memory implementation of EquityHoldingRepository."""
    
    def __init__(self):
        self._holdings: Dict[UUID, dict] = {}

    def find_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        conn=None
    ) -> List[EquityHolding]:
        holdings = [
            self._row_to_holding(row) 
            for row in self._holdings.values() 
            if row['portfolio_id'] == portfolio_id
        ]
        return holdings[offset:offset + limit]

    def get(self, holding_id: UUID, conn=None) -> Optional[EquityHolding]:
        row = self._holdings.get(holding_id)
        return self._row_to_holding(row) if row else None

    def find_by_portfolio_and_equity(
        self, 
        portfolio_id: UUID, 
        equity_id: UUID, 
        conn=None
    ) -> Optional[EquityHolding]:
        for row in self._holdings.values():
            if row['portfolio_id'] == portfolio_id and row['equity_id'] == equity_id:
                return self._row_to_holding(row)
        return None

    def save(self, holding: EquityHolding, conn=None) -> None:
        # Check for duplicate holding for the same equity in the same portfolio
        existing = self.find_by_portfolio_and_equity(
            holding.portfolio_id, holding.equity_id, conn
        )
        if existing and existing.id != holding.id:
            raise DuplicateHoldingError(holding.portfolio_id, holding.equity_id)
        
        self._holdings[holding.id] = self._holding_to_row(holding)

    def delete(self, holding_id: UUID, conn=None) -> None:
        self._holdings.pop(holding_id, None)

    def batch_save(self, holdings: List[EquityHolding], conn=None) -> None:
        for holding in holdings:
            self.save(holding, conn)

    def exists(self, holding_id: UUID, conn=None) -> bool:
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


class InMemoryCashHoldingRepository:
    """In-memory implementation of CashHoldingRepository."""
    
    def __init__(self):
        self._holdings: Dict[UUID, dict] = {}

    def find_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        conn=None
    ) -> List[CashHolding]:
        holdings = [
            self._row_to_cash_holding(row) 
            for row in self._holdings.values() 
            if row['portfolio_id'] == portfolio_id
        ]
        return holdings[offset:offset + limit]

    def get(self, holding_id: UUID, conn=None) -> Optional[CashHolding]:
        row = self._holdings.get(holding_id)
        return self._row_to_cash_holding(row) if row else None

    def find_by_portfolio_and_currency(
        self, 
        portfolio_id: UUID, 
        currency: str, 
        conn=None
    ) -> Optional[CashHolding]:
        for row in self._holdings.values():
            if row['portfolio_id'] == portfolio_id and row['currency'] == currency:
                return self._row_to_cash_holding(row)
        return None

    def save(self, cash_holding: CashHolding, conn=None) -> None:
        self._holdings[cash_holding.id] = self._cash_holding_to_row(cash_holding)

    def delete(self, holding_id: UUID, conn=None) -> None:
        self._holdings.pop(holding_id, None)

    def batch_save(self, holdings: List[CashHolding], conn=None) -> None:
        for holding in holdings:
            self.save(holding, conn)

    def exists(self, holding_id: UUID, conn=None) -> bool:
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


class InMemoryActivityReportEntryRepository:
    """In-memory implementation of ActivityReportEntryRepository."""
    
    def __init__(self):
        self._entries: Dict[UUID, dict] = {}

    def find_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        activity_type: Optional[str] = None, 
        conn=None
    ) -> List[ActivityReportEntry]:
        entries = [
            self._row_to_entry(row) 
            for row in self._entries.values() 
            if row['portfolio_id'] == portfolio_id and (
                activity_type is None or row['activity_type'] == activity_type
            )
        ]
        return entries[offset:offset + limit]

    def get(self, entry_id: UUID, conn=None) -> Optional[ActivityReportEntry]:
        row = self._entries.get(entry_id)
        return self._row_to_entry(row) if row else None

    def find_by_date_range(
        self, 
        portfolio_id: UUID, 
        start_date: str, 
        end_date: str, 
        conn=None
    ) -> List[ActivityReportEntry]:
        return [
            self._row_to_entry(row) 
            for row in self._entries.values() 
            if (row['portfolio_id'] == portfolio_id and 
                start_date <= row['date'] <= end_date)
        ]

    def save(self, entry: ActivityReportEntry, conn=None) -> None:
        self._entries[entry.id] = self._entry_to_row(entry)

    def delete(self, entry_id: UUID, conn=None) -> None:
        self._entries.pop(entry_id, None)

    def batch_save(self, entries: List[ActivityReportEntry], conn=None) -> None:
        for entry in entries:
            self.save(entry, conn)

    def exists(self, entry_id: UUID, conn=None) -> bool:
        return entry_id in self._entries

    def _entry_to_row(self, entry: ActivityReportEntry) -> dict:
        return {
            'id': entry.id,
            'portfolio_id': entry.portfolio_id,
            'equity_id': entry.equity_id,
            'currency': entry.currency,
            'activity_type': entry.activity_type,
            'amount': entry.amount,
            'date': entry.date,
            'raw_data': entry.raw_data,
            'created_at': entry.created_at,
        }

    def _row_to_entry(self, row: dict) -> ActivityReportEntry:
        """Create an ActivityReportEntry object without triggering events."""
        entry = ActivityReportEntry.__new__(ActivityReportEntry)
        entry._events = []  # Initialize the events list
        entry.id = row['id']
        entry.portfolio_id = row['portfolio_id']
        entry.equity_id = row['equity_id']
        entry.currency = row['currency']
        entry.activity_type = row['activity_type']
        entry.amount = row['amount']
        entry.date = row['date']
        entry.raw_data = row['raw_data']
        entry.created_at = row['created_at']
        return entry


class InMemoryHoldingRepository:
    """Unified in-memory repository for both equity and cash holdings."""
    
    def __init__(self):
        self.equity_holding_repo = InMemoryEquityHoldingRepository()
        self.cash_holding_repo = InMemoryCashHoldingRepository()
    
    def find_equity_holdings_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        conn=None
    ) -> List[EquityHolding]:
        return self.equity_holding_repo.find_by_portfolio_id(
            portfolio_id, limit=limit, offset=offset, conn=conn
        )
    
    def find_cash_holdings_by_portfolio_id(
        self, 
        portfolio_id: UUID, 
        *, 
        limit: int = 100, 
        offset: int = 0, 
        conn=None
    ) -> List[CashHolding]:
        return self.cash_holding_repo.find_by_portfolio_id(
            portfolio_id, limit=limit, offset=offset, conn=conn
        )
    
    def get_equity_holding(self, holding_id: UUID, conn=None) -> Optional[EquityHolding]:
        return self.equity_holding_repo.get(holding_id, conn=conn)
    
    def get_cash_holding(self, holding_id: UUID, conn=None) -> Optional[CashHolding]:
        return self.cash_holding_repo.get(holding_id, conn=conn)
    
    def find_equity_by_portfolio_and_stock(
        self, 
        portfolio_id: UUID, 
        stock_id: UUID, 
        conn=None
    ) -> Optional[EquityHolding]:
        return self.equity_holding_repo.find_by_portfolio_and_equity(
            portfolio_id, stock_id, conn=conn
        )
    
    def find_cash_by_portfolio_and_currency(
        self, 
        portfolio_id: UUID, 
        currency: str, 
        conn=None
    ) -> Optional[CashHolding]:
        return self.cash_holding_repo.find_by_portfolio_and_currency(
            portfolio_id, currency, conn=conn
        )
    
    def save_equity_holding(self, holding: EquityHolding, conn=None) -> None:
        self.equity_holding_repo.save(holding, conn=conn)
    
    def save_cash_holding(self, holding: CashHolding, conn=None) -> None:
        self.cash_holding_repo.save(holding, conn=conn)
    
    def delete_equity_holding(self, holding_id: UUID, conn=None) -> None:
        self.equity_holding_repo.delete(holding_id, conn=conn)
    
    def delete_cash_holding(self, holding_id: UUID, conn=None) -> None:
        self.cash_holding_repo.delete(holding_id, conn=conn)
    
    def batch_save_equity_holdings(self, holdings: List[EquityHolding], conn=None) -> None:
        self.equity_holding_repo.batch_save(holdings, conn=conn)
    
    def batch_save_cash_holdings(self, holdings: List[CashHolding], conn=None) -> None:
        self.cash_holding_repo.batch_save(holdings, conn=conn)


# Alias for backward compatibility - Stock and Equity are the same concept
InMemoryStockRepository = InMemoryEquityRepository
