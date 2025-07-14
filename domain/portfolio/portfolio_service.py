from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from .models.portfolio import Portfolio, PortfolioName
from .models.holding import EquityHolding, CashHolding
from .models.activity_report_entry import ActivityReportEntry
from .models.enums import Currency
from .models.import_result import ImportResult
from .repository.base import (
    PortfolioRepository, EquityRepository, EquityHoldingRepository, 
    CashHoldingRepository, ActivityReportEntryRepository
)
from .holdings_management_service import HoldingsManagementService
from .activity_management_service import ActivityManagementService
from .ibkr_import_service import IBKRImportService

class PortfolioService:
    """Simplified service layer for portfolio operations.
    
    This service provides a single entry point for portfolio modifications
    through IBKR activity report ingestion. All other operations are handled
    internally by specialized services.
    """
    
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
        
        # Initialize specialized services
        self._holdings_service = HoldingsManagementService(
            portfolio_repo, equity_repo, equity_holding_repo, cash_holding_repo
        )
        self._activity_service = ActivityManagementService(
            portfolio_repo, equity_repo, activity_entry_repo
        )
        self._ibkr_import_service = IBKRImportService(
            portfolio_repo, self._holdings_service, self._activity_service
        )

    # ================================================================
    # PUBLIC INTERFACE - Single entry point for portfolio modifications
    # ================================================================
    
    def import_from_ibkr(
        self, 
        portfolio_id: UUID, 
        trades: List[dict], 
        dividends: List[dict], 
        positions: List[dict], 
        forex_balances: Optional[List[dict]] = None, 
        conn=None
    ) -> ImportResult:
        """Import data from IBKR CSV parser results.
        
        This is the single entry point for modifying portfolio holdings.
        All portfolio modifications are driven by activity report ingestion.
        """
        return self._ibkr_import_service.import_from_ibkr(
            portfolio_id, trades, dividends, positions, forex_balances, conn
        )

    # ================================================================
    # PORTFOLIO MANAGEMENT - Basic CRUD operations
    # ================================================================

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

    # ================================================================
    # INTERNAL DELEGATION METHODS
    # ================================================================
    
    def add_equity_holding(
        self, 
        portfolio_id: UUID, 
        symbol: str, 
        quantity: Decimal, 
        cost_basis: Decimal,
        exchange: str = "NASDAQ",
        conn=None
    ) -> Optional[EquityHolding]:
        """Add an equity holding to a portfolio.
        
        Delegated to HoldingsManagementService internally.
        """
        return self._holdings_service.add_equity_holding(
            portfolio_id, symbol, quantity, cost_basis, exchange, conn
        )

    def update_equity_holding(
        self, 
        holding_id: UUID, 
        quantity: Optional[Decimal] = None,
        cost_basis: Optional[Decimal] = None,
        current_value: Optional[Decimal] = None,
        conn=None
    ) -> bool:
        """Update an equity holding.
        
        Delegated to HoldingsManagementService internally.
        """
        return self._holdings_service.update_equity_holding(
            holding_id, quantity, cost_basis, current_value, conn
        )

    def get_equity_holdings(self, portfolio_id: UUID, conn=None) -> List[EquityHolding]:
        """Get all equity holdings for a portfolio.
        
        Delegated to HoldingsManagementService internally.
        """
        return self._holdings_service.get_equity_holdings(portfolio_id, conn)

    def update_cash_balance(
        self, 
        portfolio_id: UUID, 
        new_balance_or_currency, 
        reason_or_new_balance, 
        reason: str = "manual",
        conn=None
    ) -> bool:
        """Update cash balance for a specific currency.
        
        Delegated to HoldingsManagementService internally.
        """
        return self._holdings_service.update_cash_balance(
            portfolio_id, new_balance_or_currency, reason_or_new_balance, reason, conn
        )

    def get_cash_holdings(self, portfolio_id: UUID, conn=None) -> List[CashHolding]:
        """Get all cash holdings for a portfolio.
        
        Delegated to HoldingsManagementService internally.
        """
        return self._holdings_service.get_cash_holdings(portfolio_id, conn)

    def add_activity_entry(
        self,
        portfolio_id: UUID,
        activity_type: str,
        amount: Decimal,
        date: datetime,
        stock_symbol: Optional[str] = None,
        raw_data: Optional[dict] = None
    ) -> Optional[ActivityReportEntry]:
        """Add an activity report entry to a portfolio.
        
        Delegated to ActivityManagementService internally.
        """
        return self._activity_service.add_activity_entry(
            portfolio_id, activity_type, amount, date, stock_symbol, raw_data
        )

    def get_activity_entries(
        self, 
        portfolio_id: UUID, 
        activity_type: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0,
        conn=None
    ) -> List[ActivityReportEntry]:
        """Get activity entries for a portfolio.
        
        Delegated to ActivityManagementService internally.
        """
        return self._activity_service.get_activity_entries(
            portfolio_id, activity_type, limit, offset, conn
        )

    def get_holdings(self, portfolio_id: UUID, limit: int = 100, offset: int = 0) -> List[EquityHolding]:
        """Get holdings for a portfolio. Alias for get_equity_holdings."""
        return self.get_equity_holdings(portfolio_id)
