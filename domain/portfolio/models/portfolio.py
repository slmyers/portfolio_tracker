from uuid import UUID
from datetime import datetime
from core.domain_model import DomainModel
from ..portfolio_events import (
    PortfolioCreated, PortfolioRenamed, PortfolioDeleted, HoldingAdded, 
    HoldingRemoved, ActivityReportEntryAdded, 
    ActivityReportEntryRemoved, PortfolioRecalculated,
    PortfolioImported, PortfolioExported
)
from ..portfolio_errors import (
    InvalidPortfolioNameError,
    OwnershipMismatchError, StockNotFoundError
)
from typing import Optional
from .holding import EquityHolding, CashHolding
from .activity_report_entry import ActivityReportEntry

class PortfolioName:
    """Value object for portfolio name validation and normalization."""
    MAX_LENGTH = 100

    def __init__(self, value: str):
        value = value.strip()
        if not value:
            raise InvalidPortfolioNameError(value, "Portfolio name cannot be empty")
        if len(value) > self.MAX_LENGTH:
            raise InvalidPortfolioNameError(value, f"Portfolio name must be at most {self.MAX_LENGTH} characters")
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return isinstance(other, PortfolioName) and self.value == other.value

    def __hash__(self):
        return hash(self.value)

class Portfolio(DomainModel):
    """Portfolio aggregate root."""
    
    def __init__(
        self,
        id: UUID,
        tenant_id: UUID,
        name: PortfolioName,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        super().__init__()
        self.id = id
        self.tenant_id = tenant_id
        self.name = name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        
        # Record creation event if this is a new portfolio
        if created_at is None:
            self.record_event(PortfolioCreated(
                portfolio_id=self.id,
                tenant_id=self.tenant_id,
                name=str(self.name),
                occurred_at=self.created_at
            ))

    def rename(self, new_name: PortfolioName):
        """Rename the portfolio."""
        if self.name != new_name:
            old_name = str(self.name)
            self.name = new_name
            self.updated_at = datetime.utcnow()
            self.record_event(PortfolioRenamed(
                portfolio_id=self.id,
                tenant_id=self.tenant_id,
                old_name=old_name,
                new_name=str(new_name),
                occurred_at=self.updated_at
            ))

    def delete(self):
        """Mark the portfolio as deleted."""
        self.updated_at = datetime.utcnow()
        self.record_event(PortfolioDeleted(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            occurred_at=self.updated_at
        ))

    def add_equity_holding(self, holding: EquityHolding, equity_repository):
        """Add an equity holding to the portfolio with validation."""
        # Validate ownership
        if holding.portfolio_id != self.id:
            raise OwnershipMismatchError(self.id, holding.portfolio_id)
        
        # Validate equity exists
        equity = equity_repository.get(holding.equity_id)
        if not equity:
            raise StockNotFoundError(holding.equity_id)
        
        self.updated_at = datetime.utcnow()
        
        # Set tenant_id on holding events
        events = holding.pull_events()
        for event in events:
            if hasattr(event, 'tenant_id') and event.tenant_id is None:
                event.tenant_id = self.tenant_id
        
        self.record_event(HoldingAdded(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            holding_id=holding.id,
            stock_id=holding.equity_id,  # For compatibility with events
            quantity=holding.quantity,
            cost_basis=holding.cost_basis,
            occurred_at=self.updated_at
        ))

    def remove_equity_holding(self, holding_id: UUID, equity_id: UUID):
        """Remove an equity holding from the portfolio."""
        self.updated_at = datetime.utcnow()
        self.record_event(HoldingRemoved(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            holding_id=holding_id,
            stock_id=equity_id,  # For compatibility with events
            occurred_at=self.updated_at
        ))

    def add_cash_holding(self, cash_holding: CashHolding):
        """Add a cash holding to the portfolio with validation."""
        # Validate ownership
        if cash_holding.portfolio_id != self.id:
            raise OwnershipMismatchError(self.id, cash_holding.portfolio_id)
        
        self.updated_at = datetime.utcnow()
        
        # Set tenant_id on cash holding events
        events = cash_holding.pull_events()
        for event in events:
            if hasattr(event, 'tenant_id') and event.tenant_id is None:
                event.tenant_id = self.tenant_id

    def update_cash_holding(self, cash_holding: CashHolding):
        """Update a cash holding in the portfolio with validation."""
        # Validate ownership
        if cash_holding.portfolio_id != self.id:
            raise OwnershipMismatchError(self.id, cash_holding.portfolio_id)
        
        self.updated_at = datetime.utcnow()
        
        # Set tenant_id on cash holding events
        events = cash_holding.pull_events()
        for event in events:
            if hasattr(event, 'tenant_id') and event.tenant_id is None:
                event.tenant_id = self.tenant_id

    def add_activity_entry(self, entry: ActivityReportEntry, equity_repository=None):
        """Add an activity report entry to the portfolio with validation."""
        # Validate ownership
        if entry.portfolio_id != self.id:
            raise OwnershipMismatchError(self.id, entry.portfolio_id)
        
        # Validate equity exists if equity_id is provided
        if entry.equity_id and equity_repository:
            equity = equity_repository.get(entry.equity_id)
            if not equity:
                raise StockNotFoundError(entry.equity_id)
        
        self.updated_at = datetime.utcnow()
        self.record_event(ActivityReportEntryAdded(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            activity_entry_id=entry.id,
            stock_id=entry.equity_id,  # For compatibility with events
            activity_type=entry.activity_type,
            amount=entry.amount,
            occurred_at=self.updated_at
        ))

    def remove_activity_entry(self, entry_id: UUID):
        """Remove an activity report entry from the portfolio."""
        self.updated_at = datetime.utcnow()
        self.record_event(ActivityReportEntryRemoved(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            activity_entry_id=entry_id,
            occurred_at=self.updated_at
        ))

    def recalculate(self, recalculation_type: str = 'manual'):
        """Mark the portfolio as recalculated."""
        self.updated_at = datetime.utcnow()
        self.record_event(PortfolioRecalculated(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            recalculation_type=recalculation_type,
            occurred_at=self.updated_at
        ))

    def mark_imported(self, source: str, entries_count: int):
        """Mark the portfolio as imported from an external source."""
        self.updated_at = datetime.utcnow()
        self.record_event(PortfolioImported(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            source=source,
            entries_count=entries_count,
            occurred_at=self.updated_at
        ))

    def mark_exported(self, export_format: str, export_purpose: str):
        """Mark the portfolio as exported."""
        self.updated_at = datetime.utcnow()
        self.record_event(PortfolioExported(
            portfolio_id=self.id,
            tenant_id=self.tenant_id,
            export_format=export_format,
            export_purpose=export_purpose,
            occurred_at=self.updated_at
        ))
