from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from .models.portfolio import Portfolio, PortfolioName
from .models.holding import Equity, EquityHolding, CashHolding
from .models.activity_report_entry import ActivityReportEntry
from .models.enums import Currency, Exchange
from .models.import_result import ImportResult
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

    def create_portfolio(self, tenant_id: UUID, name: str, portfolio_id: Optional[UUID] = None, conn=None) -> Portfolio:
        """Create a new portfolio within a transaction."""
        portfolio = Portfolio(
            id=portfolio_id or uuid4(),
            tenant_id=tenant_id,
            name=PortfolioName(name)
        )
        self.portfolio_repo.save(portfolio, conn=conn)  # Save portfolio first
        
        # Create initial cash holding in CAD
        cash_holding = CashHolding(
            id=uuid4(),
            portfolio_id=portfolio.id,
            currency=Currency.CAD,
            balance=Decimal('0')
        )
        self.cash_holding_repo.save(cash_holding, conn=conn)  # Save cash holding within the same transaction
        
        # Return the portfolio with cash_balance calculated by the repository
        return self.portfolio_repo.get(portfolio.id, conn=conn)

    def get_portfolio(self, portfolio_id: UUID, conn=None) -> Optional[Portfolio]:
        """Get a portfolio by ID."""
        return self.portfolio_repo.get(portfolio_id, conn=conn)

    def get_portfolios_by_tenant(self, tenant_id: UUID, conn=None) -> List[Portfolio]:
        """Get all portfolios for a tenant."""
        return self.portfolio_repo.find_by_tenant_id(tenant_id, conn=conn)

    def rename_portfolio(self, portfolio_id: UUID, new_name: str, conn=None) -> bool:
        """Rename a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return False
        
        portfolio.rename(PortfolioName(new_name))
        self.portfolio_repo.save(portfolio, conn=conn)
        return True

    def delete_portfolio(self, portfolio_id: UUID, conn=None) -> bool:
        """Delete a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return False
        
        portfolio.delete()
        self.portfolio_repo.delete(portfolio_id, conn=conn)
        return True

    def add_equity_holding(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        quantity: Decimal, 
        cost_basis: Decimal,
        exchange: str = "NASDAQ",
        conn=None
    ) -> Optional[EquityHolding]:
        """Add an equity holding to a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return None
        
        # Get or create equity
        equity = self.equity_repo.find_by_symbol(symbol, exchange, conn=conn)
        if not equity:
            equity = Equity(
                id=uuid4(),
                symbol=symbol,
                exchange=Exchange(exchange) if exchange in Exchange.__members__ else None
            )
            self.equity_repo.save(equity, conn=conn)
        
        # Check for duplicate holding
        existing_holding = self.equity_holding_repo.find_by_portfolio_and_equity(
            portfolio_id, equity.id, conn=conn
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
        self.equity_holding_repo.save(holding, conn=conn)
        self.portfolio_repo.save(portfolio, conn=conn)
        
        return holding

    def update_equity_holding(
        self, 
        holding_id: UUID, 
        quantity: Optional[Decimal] = None,
        cost_basis: Optional[Decimal] = None,
        current_value: Optional[Decimal] = None,
        conn=None
    ) -> bool:
        """Update an equity holding."""
        holding = self.equity_holding_repo.get(holding_id, conn=conn)
        if not holding:
            return False
        
        if quantity is not None:
            holding.update_quantity(quantity)
        if cost_basis is not None:
            holding.update_cost_basis(cost_basis)
        if current_value is not None:
            holding.update_current_value(current_value)
        
        self.equity_holding_repo.save(holding, conn=conn)
        return True

    def remove_equity_holding(self, holding_id: UUID, conn=None) -> bool:
        """Remove an equity holding."""
        holding = self.equity_holding_repo.get(holding_id, conn=conn)
        if not holding:
            return False
        
        portfolio = self.portfolio_repo.get(holding.portfolio_id, conn=conn)
        if portfolio:
            portfolio.remove_equity_holding(holding.id, holding.equity_id)
            self.portfolio_repo.save(portfolio, conn=conn)
        
        self.equity_holding_repo.delete(holding_id, conn=conn)
        return True

    def get_equity_holdings(self, portfolio_id: UUID, conn=None) -> List[EquityHolding]:
        """Get all equity holdings for a portfolio."""
        return self.equity_holding_repo.find_by_portfolio_id(portfolio_id, conn=conn)

    def update_cash_balance(
        self, 
        portfolio_id: UUID, 
        new_balance_or_currency, 
        reason_or_new_balance, 
        reason: str = "manual",
        conn=None
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
            
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return False
        
        # Get or create cash holding
        cash_holding = self.cash_holding_repo.find_by_portfolio_and_currency(
            portfolio_id, currency.value, conn=conn
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
        
        self.cash_holding_repo.save(cash_holding, conn=conn)
        self.portfolio_repo.save(portfolio, conn=conn)
        return True

    def get_cash_holdings(self, portfolio_id: UUID, conn=None) -> List[CashHolding]:
        """Get all cash holdings for a portfolio."""
        return self.cash_holding_repo.find_by_portfolio_id(portfolio_id, conn=conn)

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

        # Determine currency from raw_data if available
        currency = Currency.USD  # Default fallback
        if raw_data and 'currency' in raw_data:
            currency_str = raw_data['currency']
            if currency_str and currency_str in Currency.__members__:
                currency = Currency(currency_str)

        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=portfolio_id,
            equity_id=equity_id,
            activity_type=activity_type,
            amount=amount,
            currency=currency,
            date=date,
            raw_data=raw_data
        )

        # Add to portfolio (triggers validation and events)
        portfolio.add_activity_entry(entry, self.equity_repo)
        
        # Save both
        self.activity_entry_repo.save(entry)
        self.portfolio_repo.save(portfolio)
        
        return entry

    def _add_activity_entry_with_conn(
        self,
        portfolio_id: UUID,
        activity_type: str,
        amount: Decimal,
        date: datetime,
        stock_symbol: Optional[str] = None,
        raw_data: Optional[dict] = None,
        currency: Optional[Currency] = None,
        conn=None
    ) -> Optional[ActivityReportEntry]:
        """Add an activity report entry with connection support."""
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return None

        equity_id = None
        if stock_symbol:
            equity = self.equity_repo.find_by_symbol(stock_symbol, "NASDAQ", conn=conn)  # Default to NASDAQ
            if not equity:
                equity = Equity(
                    id=uuid4(),
                    symbol=stock_symbol,
                    name=stock_symbol,  # Use symbol as name for now
                    exchange=Exchange.NASDAQ
                )
                self.equity_repo.save(equity, conn=conn)
            equity_id = equity.id

        # Determine currency from raw_data if not provided
        if currency is None:
            currency_str = raw_data.get('currency') if raw_data else None
            if currency_str and currency_str in Currency.__members__:
                currency = Currency(currency_str)
            else:
                currency = Currency.USD  # Default fallback

        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=portfolio_id,
            equity_id=equity_id,
            activity_type=activity_type,
            amount=amount,
            currency=currency,
            date=date,
            raw_data=raw_data
        )

        # Add to portfolio (triggers validation and events)
        portfolio.add_activity_entry(entry, self.equity_repo)
        
        # Save both
        self.activity_entry_repo.save(entry, conn=conn)
        self.portfolio_repo.save(portfolio, conn=conn)
        
        return entry

    def _add_equity_holding_with_conn(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        quantity: Decimal, 
        cost_basis: Decimal,
        exchange: str = "NASDAQ",
        conn=None
    ) -> Optional[EquityHolding]:
        """Add an equity holding with connection support."""
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return None
        
        # Get or create equity
        equity = self.equity_repo.find_by_symbol(symbol, exchange, conn=conn)
        if not equity:
            equity = Equity(
                id=uuid4(),
                symbol=symbol,
                exchange=Exchange(exchange) if exchange in Exchange.__members__ else None
            )
            self.equity_repo.save(equity, conn=conn)
        
        # Check for duplicate holding
        existing_holding = self.equity_holding_repo.find_by_portfolio_and_equity(
            portfolio_id, equity.id, conn=conn
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
        self.equity_holding_repo.save(holding, conn=conn)
        self.portfolio_repo.save(portfolio, conn=conn)
        
        return holding

    def get_holdings(self, portfolio_id: UUID, limit: int = 100, offset: int = 0) -> List[EquityHolding]:
        """Get holdings for a portfolio."""
        return self.equity_holding_repo.find_by_portfolio_id(portfolio_id, limit=limit, offset=offset)

    def get_activity_entries(
        self, 
        portfolio_id: UUID, 
        activity_type: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0,
        conn=None
    ) -> List[ActivityReportEntry]:
        """Get activity entries for a portfolio."""
        return self.activity_entry_repo.find_by_portfolio_id(
            portfolio_id, 
            activity_type=activity_type, 
            limit=limit, 
            offset=offset,
            conn=conn
        )

    def import_from_ibkr(self, portfolio_id: UUID, trades: List[dict], dividends: List[dict], positions: List[dict], forex_balances: Optional[List[dict]] = None, conn=None) -> ImportResult:
        """Import data from IBKR CSV parser results."""
        # Initialize result object
        result = ImportResult(
            success=False,
            import_source='IBKR_CSV',
            portfolio_id=str(portfolio_id),
            started_at=datetime.now()
        )
        
        try:
            # Validate portfolio exists
            portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
            if not portfolio:
                result.mark_failure(f"Portfolio with ID {portfolio_id} not found", "PortfolioNotFoundError")
                return result

            # Import trades as activity entries
            for trade in trades:
                if not trade.get('symbol') or not trade.get('datetime'):
                    result.add_warning(f"Skipping trade missing symbol or datetime: {trade}")
                    result.skipped_trades += 1
                    continue
                    
                try:
                    # Parse IBKR datetime format: "2025-02-12, 12:33:43"
                    trade_datetime = trade['datetime']
                    if isinstance(trade_datetime, str):
                        try:
                            # Try ISO format first
                            trade_datetime = datetime.fromisoformat(trade_datetime)
                        except ValueError:
                            # Try IBKR format: "YYYY-MM-DD, HH:MM:SS"
                            trade_datetime = datetime.strptime(trade_datetime, "%Y-%m-%d, %H:%M:%S")
                    
                    entry = self._add_activity_entry_with_conn(
                        portfolio_id=portfolio_id,
                        activity_type='TRADE',
                        amount=trade.get('proceeds', Decimal('0')),
                        date=trade_datetime,
                        stock_symbol=trade['symbol'],
                        raw_data=trade,
                        conn=conn
                    )
                    
                    if entry:
                        result.trades_imported += 1
                        result.activity_entries_created += 1
                    else:
                        result.add_failed_item('trade', trade, 'Failed to create activity entry')
                        
                except Exception as e:
                    result.add_failed_item('trade', trade, str(e))

            # Import dividends as activity entries
            for dividend in dividends:
                if not dividend.get('description') or not dividend.get('date'):
                    result.add_warning(f"Skipping dividend missing description or date: {dividend}")
                    result.skipped_dividends += 1
                    continue
                    
                try:
                    # Parse dividend date - usually in YYYY-MM-DD format
                    dividend_date = dividend['date']
                    if isinstance(dividend_date, str):
                        try:
                            # Try ISO format first
                            dividend_date = datetime.fromisoformat(dividend_date)
                        except ValueError:
                            # Try just date format
                            dividend_date = datetime.strptime(dividend_date, "%Y-%m-%d")
                    
                    entry = self._add_activity_entry_with_conn(
                        portfolio_id=portfolio_id,
                        activity_type='DIVIDEND',
                        amount=dividend.get('amount', Decimal('0')),
                        date=dividend_date,
                        raw_data=dividend,
                        conn=conn
                    )
                    
                    if entry:
                        result.dividends_imported += 1
                        result.activity_entries_created += 1
                    else:
                        result.add_failed_item('dividend', dividend, 'Failed to create activity entry')
                        
                except Exception as e:
                    result.add_failed_item('dividend', dividend, str(e))

            # Import positions as holdings
            for position in positions:
                if not position.get('symbol') or not position.get('quantity'):
                    result.add_warning(f"Skipping position missing symbol or quantity: {position}")
                    result.skipped_positions += 1
                    continue
                    
                try:
                    quantity = Decimal(str(position['quantity']))
                    cost_basis = Decimal(str(position.get('cost_basis', 0)))
                    
                    # Check if equity already exists to track new equity creation
                    existing_equity = self.equity_repo.find_by_symbol(position['symbol'], "NASDAQ", conn=conn)
                    equity_created = existing_equity is None
                    
                    # Try to add the holding (this will create the equity if needed)
                    holding = self._add_equity_holding_with_conn(
                        portfolio_id=portfolio_id,
                        symbol=position['symbol'],
                        quantity=quantity,
                        cost_basis=cost_basis,
                        exchange="NASDAQ",  # Default exchange
                        conn=conn
                    )
                    
                    if holding:
                        result.positions_imported += 1
                        result.equity_holdings_created += 1
                        if equity_created:
                            result.equities_created += 1
                    else:
                        result.add_failed_item('position', position, 'Failed to create equity holding')
                        
                except DuplicateHoldingError:
                    result.add_warning(f"Duplicate holding for {position['symbol']} - skipping")
                    result.skipped_positions += 1
                except ValueError as e:
                    result.add_failed_item('position', position, f'Invalid numeric value: {str(e)}')
                except Exception as e:
                    result.add_failed_item('position', position, str(e))

            # Import forex balances as cash holdings
            if forex_balances:
                for forex_balance in forex_balances:
                    if not forex_balance.get('currency') or not forex_balance.get('quantity'):
                        result.add_warning(f"Skipping forex balance missing currency or quantity: {forex_balance}")
                        continue
                        
                    try:
                        currency_str = forex_balance['currency']
                        quantity = Decimal(str(forex_balance['quantity']))
                        
                        # Convert currency string to Currency enum
                        if currency_str not in Currency.__members__:
                            result.add_warning(f"Unsupported currency '{currency_str}' in forex balance - skipping")
                            continue
                            
                        currency = Currency(currency_str)
                        
                        # Get or create cash holding for this currency
                        cash_holding = self.cash_holding_repo.find_by_portfolio_and_currency(
                            portfolio_id, currency.value, conn=conn
                        )
                        
                        if not cash_holding:
                            # Create new cash holding
                            cash_holding = CashHolding(
                                id=uuid4(),
                                portfolio_id=portfolio_id,
                                currency=currency,
                                balance=quantity
                            )
                            result.cash_holdings_created += 1
                        else:
                            # Update existing cash holding
                            cash_holding.update_balance(quantity, "IBKR_FOREX_IMPORT")
                        
                        # Save the cash holding
                        self.cash_holding_repo.save(cash_holding, conn=conn)
                        
                        # Add to portfolio (triggers validation and events)
                        portfolio.add_cash_holding(cash_holding)
                        
                        # Update result counters
                        result.forex_balances_imported += 1
                        
                    except ValueError as e:
                        result.add_failed_item('forex_balance', forex_balance, f'Invalid numeric value: {str(e)}')
                    except Exception as e:
                        result.add_failed_item('forex_balance', forex_balance, str(e))

            # Mark portfolio as imported with total activity entries created
            portfolio.mark_imported('IBKR_CSV', result.activity_entries_created)
            self.portfolio_repo.save(portfolio, conn=conn)
            
            # Mark as successful
            result.mark_success()
            
        except Exception as e:
            result.mark_failure(f"Unexpected error during import: {str(e)}", type(e).__name__)
        
        return result
