from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from .models.holding import Equity, EquityHolding, CashHolding
from .models.enums import Currency, Exchange
from .portfolio_errors import DuplicateHoldingError
from .repository.base import (
    PortfolioRepository, EquityRepository, EquityHoldingRepository, 
    CashHoldingRepository
)

class HoldingsManagementService:
    """Service for managing portfolio holdings (equity and cash)."""
    
    def __init__(
        self,
        portfolio_repo: PortfolioRepository,
        equity_repo: EquityRepository,
        equity_holding_repo: EquityHoldingRepository,
        cash_holding_repo: CashHoldingRepository
    ):
        self.portfolio_repo = portfolio_repo
        self.equity_repo = equity_repo
        self.equity_holding_repo = equity_holding_repo
        self.cash_holding_repo = cash_holding_repo
    
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
        from uuid import uuid4
        
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
        from uuid import uuid4
        
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
