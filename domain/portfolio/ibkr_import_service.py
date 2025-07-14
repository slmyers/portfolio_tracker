from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from .models.import_result import ImportResult
from .models.enums import Currency
from .portfolio_errors import DuplicateHoldingError
from .holdings_management_service import HoldingsManagementService
from .activity_management_service import ActivityManagementService
from .repository.base import PortfolioRepository

class IBKRImportService:
    """Service for coordinating IBKR data import and portfolio updates."""
    
    def __init__(
        self,
        portfolio_repo: PortfolioRepository,
        holdings_service: HoldingsManagementService,
        activity_service: ActivityManagementService
    ):
        self.portfolio_repo = portfolio_repo
        self.holdings_service = holdings_service
        self.activity_service = activity_service
    
    def import_from_ibkr(
        self, 
        portfolio_id: UUID, 
        trades: List[dict], 
        dividends: List[dict], 
        positions: List[dict], 
        forex_balances: Optional[List[dict]] = None, 
        conn=None
    ) -> ImportResult:
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
                    
                    entry = self.activity_service.add_activity_entry(
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
                    
                    entry = self.activity_service.add_activity_entry(
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
                    from .repository.base import EquityRepository
                    if hasattr(self.holdings_service, 'equity_repo'):
                        existing_equity = self.holdings_service.equity_repo.find_by_symbol(position['symbol'], "NASDAQ", conn=conn)
                        equity_created = existing_equity is None
                    else:
                        equity_created = False  # Fallback if we can't check
                    
                    # Try to add the holding (this will create the equity if needed)
                    holding = self.holdings_service.add_equity_holding(
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
                        
                        # Check if cash holding already exists to track creation
                        from .repository.base import CashHoldingRepository
                        if hasattr(self.holdings_service, 'cash_holding_repo'):
                            existing_cash_holding = self.holdings_service.cash_holding_repo.find_by_portfolio_and_currency(
                                portfolio_id, currency.value, conn=conn
                            )
                            cash_holding_created = existing_cash_holding is None
                        else:
                            cash_holding_created = False  # Fallback
                        
                        # Update the cash balance using the holdings service
                        success = self.holdings_service.update_cash_balance(
                            portfolio_id=portfolio_id,
                            new_balance_or_currency=currency,
                            reason_or_new_balance=quantity,
                            reason="IBKR_FOREX_IMPORT",
                            conn=conn
                        )
                        
                        if success:
                            # Update result counters
                            result.forex_balances_imported += 1
                            if cash_holding_created:
                                result.cash_holdings_created += 1
                        else:
                            result.add_failed_item('forex_balance', forex_balance, 'Failed to update cash balance')
                            
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
