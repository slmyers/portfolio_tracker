from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from .models.activity_report_entry import ActivityReportEntry
from .models.enums import Currency
from .repository.base import (
    PortfolioRepository, EquityRepository, ActivityReportEntryRepository
)

class ActivityManagementService:
    """Service for managing portfolio activity entries."""
    
    def __init__(
        self,
        portfolio_repo: PortfolioRepository,
        equity_repo: EquityRepository,
        activity_entry_repo: ActivityReportEntryRepository
    ):
        self.portfolio_repo = portfolio_repo
        self.equity_repo = equity_repo
        self.activity_entry_repo = activity_entry_repo
    
    def add_activity_entry(
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
        """Add an activity report entry to a portfolio."""
        portfolio = self.portfolio_repo.get(portfolio_id, conn=conn)
        if not portfolio:
            return None
        
        # Get stock if symbol provided
        equity_id = None
        if stock_symbol:
            equity = self.equity_repo.find_by_symbol(stock_symbol, "NASDAQ", conn=conn)
            if not equity:
                # Create equity if it doesn't exist
                from .models.holding import Equity
                from .models.enums import Exchange
                equity = Equity(
                    id=uuid4(),
                    symbol=stock_symbol,
                    exchange=Exchange.NASDAQ
                )
                self.equity_repo.save(equity, conn=conn)
            equity_id = equity.id
        
        # Extract currency from raw_data if not provided
        if currency is None and raw_data and 'currency' in raw_data:
            currency_str = raw_data['currency']
            try:
                currency = Currency(currency_str)
            except ValueError:
                # Default to USD if invalid currency
                currency = Currency.USD
        elif currency is None:
            currency = Currency.USD
        
        # Create activity entry
        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=portfolio_id,
            equity_id=equity_id,
            activity_type=activity_type,
            amount=amount,
            date=date,
            currency=currency,
            raw_data=raw_data or {}
        )
        
        # Add to portfolio and save
        portfolio.add_activity_entry(entry, self.equity_repo)
        self.activity_entry_repo.save(entry, conn=conn)
        self.portfolio_repo.save(portfolio, conn=conn)
        
        return entry
    
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
