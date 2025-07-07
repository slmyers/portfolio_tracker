from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from .models.portfolio import Portfolio, PortfolioName
from .models.holding import Equity, EquityHolding, CashHolding
from .models.activity_report_entry import ActivityReportEntry
from .models.enums import Currency, Exchange
from .portfolio_errors import DuplicateHoldingError
from .repository.base import (
    PortfolioRepository, EquityRepository, EquityHoldingRepository, 
    CashHoldingRepository, ActivityReportEntryRepository
)

class PortfolioService:
    """Service layer for portfolio operations."""
    
    def __init__(
        self,
        portfolio_repo: PortfolioRepository,
        equity_repo: EquityRepository,
        equity_holding_repo: EquityHoldingRepository,
        cash_holding_repo: CashHoldingRepository,
        activity_entry_repo: ActivityReportEntryRepository
    ):
        self.portfolio_repo = portfolio_repo
        self.equity_repo = equity_repo
        self.equity_holding_repo = equity_holding_repo
        self.cash_holding_repo = cash_holding_repo
        self.activity_entry_repo = activity_entry_repo

    def create_portfolio(self, tenant_id: UUID, name: str) -> Portfolio:
        """Create a new portfolio."""
        portfolio = Portfolio(
            id=uuid4(),
            tenant_id=tenant_id,
            name=PortfolioName(name)
        )
        self.portfolio_repo.save(portfolio)
        
        # Create initial cash holding in USD
        cash_holding = CashHolding(
            id=uuid4(),
            portfolio_id=portfolio.id,
            currency=Currency.USD,
            balance=Decimal('0')
        )
        self.cash_holding_repo.save(cash_holding)
        
        # Return the portfolio with cash_balance calculated by the repository
        return self.portfolio_repo.get(portfolio.id)

    def get_portfolio(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Get a portfolio by ID."""
        return self.portfolio_repo.get(portfolio_id)

    def get_portfolios_by_tenant(self, tenant_id: UUID) -> List[Portfolio]:
        """Get all portfolios for a tenant."""
        return self.portfolio_repo.find_by_tenant_id(tenant_id)

    def rename_portfolio(self, portfolio_id: UUID, new_name: str) -> bool:
        """Rename a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return False
        
        portfolio.rename(PortfolioName(new_name))
        self.portfolio_repo.save(portfolio)
        return True

    def delete_portfolio(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return False
        
        portfolio.delete()
        self.portfolio_repo.delete(portfolio_id)
        return True

    def add_equity_holding(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        quantity: Decimal, 
        cost_basis: Decimal,
        exchange: str = "NASDAQ"
    ) -> Optional[EquityHolding]:
        """Add an equity holding to a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return None
        
        # Get or create equity
        equity = self.equity_repo.find_by_symbol(symbol, exchange)
        if not equity:
            equity = Equity(
                id=uuid4(),
                symbol=symbol,
                exchange=Exchange(exchange) if exchange in Exchange.__members__ else None
            )
            self.equity_repo.save(equity)
        
        # Check for duplicate holding
        existing_holding = self.equity_holding_repo.find_by_portfolio_and_equity(
            portfolio_id, equity.id
        )
        if existing_holding:
            raise DuplicateHoldingError(portfolio_id, equity.id)
        
        # Create holding
        holding = EquityHolding(
            id=uuid4(),
            portfolio_id=portfolio_id,
            equity_id=equity.id,
            quantity=quantity,
            cost_basis=cost_basis
        )
        
        # Add to portfolio and save
        portfolio.add_equity_holding(holding, self.equity_repo)
        self.equity_holding_repo.save(holding)
        self.portfolio_repo.save(portfolio)
        
        return holding

    def add_holding(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        quantity: Decimal, 
        cost_basis: Decimal,
        exchange: str = "NASDAQ"
    ) -> Optional[EquityHolding]:
        """Alias for add_equity_holding for backward compatibility."""
        return self.add_equity_holding(portfolio_id, symbol, quantity, cost_basis, exchange)

    def update_equity_holding(
        self, 
        holding_id: UUID, 
        quantity: Optional[Decimal] = None,
        cost_basis: Optional[Decimal] = None,
        current_value: Optional[Decimal] = None
    ) -> bool:
        """Update an equity holding."""
        holding = self.equity_holding_repo.get(holding_id)
        if not holding:
            return False
        
        if quantity is not None:
            holding.update_quantity(quantity)
        if cost_basis is not None:
            holding.update_cost_basis(cost_basis)
        if current_value is not None:
            holding.update_current_value(current_value)
        
        self.equity_holding_repo.save(holding)
        return True

    def remove_equity_holding(self, holding_id: UUID) -> bool:
        """Remove an equity holding."""
        holding = self.equity_holding_repo.get(holding_id)
        if not holding:
            return False
        
        portfolio = self.portfolio_repo.get(holding.portfolio_id)
        if portfolio:
            portfolio.remove_equity_holding(holding.id, holding.equity_id)
            self.portfolio_repo.save(portfolio)
        
        self.equity_holding_repo.delete(holding_id)
        return True

    def get_equity_holdings(self, portfolio_id: UUID) -> List[EquityHolding]:
        """Get all equity holdings for a portfolio."""
        return self.equity_holding_repo.find_by_portfolio_id(portfolio_id)

    def update_cash_balance(
        self, 
        portfolio_id: UUID, 
        new_balance_or_currency, 
        reason_or_new_balance, 
        reason: str = "manual"
    ) -> bool:
        """Update cash balance for a specific currency.
        
        Two call patterns supported:
        1. update_cash_balance(portfolio_id, currency, new_balance, reason="manual")
        2. update_cash_balance(portfolio_id, new_balance, reason)  # Uses USD by default
        """
        # Handle different calling patterns for backward compatibility
        if isinstance(new_balance_or_currency, Decimal):
            # Pattern 2: (portfolio_id, new_balance, reason)
            currency = Currency.USD
            new_balance = new_balance_or_currency
            reason = reason_or_new_balance if isinstance(reason_or_new_balance, str) else "manual"
        else:
            # Pattern 1: (portfolio_id, currency, new_balance, reason)
            currency = new_balance_or_currency
            new_balance = reason_or_new_balance
            
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return False
        
        # Get or create cash holding
        cash_holding = self.cash_holding_repo.find_by_portfolio_and_currency(
            portfolio_id, currency.value
        )
        if not cash_holding:
            cash_holding = CashHolding(
                id=uuid4(),
                portfolio_id=portfolio_id,
                currency=currency,
                balance=Decimal('0')
            )
        
        cash_holding.update_balance(new_balance, reason)
        portfolio.add_cash_holding(cash_holding)
        
        self.cash_holding_repo.save(cash_holding)
        self.portfolio_repo.save(portfolio)
        return True

    def get_cash_holdings(self, portfolio_id: UUID) -> List[CashHolding]:
        """Get all cash holdings for a portfolio."""
        return self.cash_holding_repo.find_by_portfolio_id(portfolio_id)

    def add_activity_entry(
        self,
        portfolio_id: UUID,
        activity_type: str,
        amount: Decimal,
        date: datetime,
        stock_symbol: Optional[str] = None,
        raw_data: Optional[dict] = None
    ) -> Optional[ActivityReportEntry]:
        """Add an activity report entry to a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return None

        equity_id = None
        if stock_symbol:
            equity = self.equity_repo.find_by_symbol(stock_symbol, "NASDAQ")  # Default to NASDAQ
            if not equity:
                equity = Equity(
                    id=uuid4(),
                    symbol=stock_symbol,
                    name=stock_symbol,  # Use symbol as name for now
                    exchange=Exchange.NASDAQ
                )
                self.equity_repo.save(equity)
            equity_id = equity.id

        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=portfolio_id,
            equity_id=equity_id,
            activity_type=activity_type,
            amount=amount,
            currency=Currency.USD,  # Default currency
            date=date,
            raw_data=raw_data
        )

        # Add to portfolio (triggers validation and events)
        portfolio.add_activity_entry(entry, self.equity_repo)
        
        # Save both
        self.activity_entry_repo.save(entry)
        self.portfolio_repo.save(portfolio)
        
        return entry

    def get_holdings(self, portfolio_id: UUID, limit: int = 100, offset: int = 0) -> List[EquityHolding]:
        """Get holdings for a portfolio."""
        return self.equity_holding_repo.find_by_portfolio_id(portfolio_id, limit=limit, offset=offset)

    def get_activity_entries(
        self, 
        portfolio_id: UUID, 
        activity_type: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[ActivityReportEntry]:
        """Get activity entries for a portfolio."""
        return self.activity_entry_repo.find_by_portfolio_id(
            portfolio_id, 
            activity_type=activity_type, 
            limit=limit, 
            offset=offset
        )

    def import_from_ibkr(self, portfolio_id: UUID, trades: List[dict], dividends: List[dict], positions: List[dict]) -> bool:
        """Import data from IBKR CSV parser results."""
        portfolio = self.portfolio_repo.get(portfolio_id)
        if not portfolio:
            return False

        entries_count = 0

        # Import trades as activity entries
        for trade in trades:
            if trade.get('symbol') and trade.get('datetime'):
                self.add_activity_entry(
                    portfolio_id=portfolio_id,
                    activity_type='TRADE',
                    amount=trade.get('proceeds', Decimal('0')),
                    date=datetime.fromisoformat(trade['datetime']) if isinstance(trade['datetime'], str) else trade['datetime'],
                    stock_symbol=trade['symbol'],
                    raw_data=trade
                )
                entries_count += 1

        # Import dividends as activity entries
        for dividend in dividends:
            if dividend.get('description') and dividend.get('date'):
                self.add_activity_entry(
                    portfolio_id=portfolio_id,
                    activity_type='DIVIDEND',
                    amount=dividend.get('amount', Decimal('0')),
                    date=datetime.fromisoformat(dividend['date']) if isinstance(dividend['date'], str) else dividend['date'],
                    raw_data=dividend
                )
                entries_count += 1

        # Import positions as holdings
        for position in positions:
            if position.get('symbol') and position.get('quantity'):
                try:
                    quantity = Decimal(str(position['quantity']))
                    cost_basis = Decimal(str(position.get('cost_basis', 0)))
                    
                    # Try to add the holding (this will create the equity if needed)
                    self.add_equity_holding(
                        portfolio_id=portfolio_id,
                        symbol=position['symbol'],
                        quantity=quantity,
                        cost_basis=cost_basis,
                        exchange="NASDAQ"  # Default exchange
                    )
                except (DuplicateHoldingError, ValueError):
                    # Skip duplicates or invalid data
                    pass

        # Mark portfolio as imported
        portfolio.mark_imported('IBKR_CSV', entries_count)
        self.portfolio_repo.save(portfolio)
        
        return True
