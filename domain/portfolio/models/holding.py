from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from core.domain_model import DomainModel
from .enums import Currency, Exchange
from ..portfolio_events import HoldingUpdated, CashBalanceUpdated
from ..portfolio_errors import NegativeCashBalanceError


class Equity(DomainModel):
    """Entity representing an equity/stock in the system."""
    
    def __init__(
        self,
        id: UUID,
        symbol: str,
        name: Optional[str] = None,
        exchange: Optional[Exchange] = None,
        created_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.symbol = symbol
        self.name = name
        self.exchange = exchange
        self.created_at = created_at or datetime.utcnow()

    def update_info(self, name: Optional[str] = None, exchange: Optional[Exchange] = None):
        """Update equity information."""
        if name is not None:
            self.name = name
        if exchange is not None:
            self.exchange = exchange

class EquityHolding(DomainModel):
    """Entity representing an equity holding in a portfolio."""
    
    def __init__(
        self, 
        id: UUID, 
        portfolio_id: UUID, 
        equity_id: UUID, 
        quantity: Decimal, 
        cost_basis: Decimal,
        current_value: Optional[Decimal] = None,
        created_at: Optional[datetime] = None, 
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.portfolio_id = portfolio_id
        self.equity_id = equity_id
        self.quantity = quantity
        self.cost_basis = cost_basis
        self.current_value = current_value or Decimal('0')
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

    @property 
    def stock_id(self) -> UUID:
        """Alias for equity_id for backward compatibility."""
        return self.equity_id

    def update_quantity(self, new_quantity: Decimal):
        """Update the quantity of this holding."""
        if new_quantity != self.quantity:
            old_quantity = self.quantity
            self.quantity = new_quantity
            self.updated_at = datetime.utcnow()
            self.record_event(HoldingUpdated(
                portfolio_id=self.portfolio_id,
                tenant_id=None,  # Will be set by portfolio aggregate
                holding_id=self.id,
                stock_id=self.equity_id,  # For compatibility with events
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                occurred_at=self.updated_at
            ))

    def update_cost_basis(self, new_cost_basis: Decimal):
        """Update the cost basis of this holding."""
        if new_cost_basis != self.cost_basis:
            old_cost_basis = self.cost_basis
            self.cost_basis = new_cost_basis
            self.updated_at = datetime.utcnow()
            self.record_event(HoldingUpdated(
                portfolio_id=self.portfolio_id,
                tenant_id=None,  # Will be set by portfolio aggregate
                holding_id=self.id,
                stock_id=self.equity_id,  # For compatibility with events
                old_cost_basis=old_cost_basis,
                new_cost_basis=new_cost_basis,
                occurred_at=self.updated_at
            ))

    def update_current_value(self, new_current_value: Decimal):
        """Update the current value of this holding."""
        self.current_value = new_current_value
        self.updated_at = datetime.utcnow()

class CashHolding(DomainModel):
    """Entity representing a cash holding in a portfolio."""
    
    def __init__(
        self,
        id: UUID,
        portfolio_id: UUID,
        currency: Currency,
        balance: Decimal,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.portfolio_id = portfolio_id
        self.currency = currency
        self.balance = balance
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at

    def update_balance(self, new_balance: Decimal, reason: str = "manual"):
        """Update the cash balance with validation."""
        if new_balance < 0:
            raise NegativeCashBalanceError(self.portfolio_id, new_balance)
        
        if new_balance != self.balance:
            old_balance = self.balance
            self.balance = new_balance
            self.updated_at = datetime.utcnow()
            self.record_event(CashBalanceUpdated(
                portfolio_id=self.portfolio_id,
                tenant_id=None,  # Will be set by portfolio aggregate
                old_balance=old_balance,
                new_balance=new_balance,
                reason=reason,
                occurred_at=self.updated_at
            ))