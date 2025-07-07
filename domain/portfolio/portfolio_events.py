from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from core.domain_event import DomainEvent
from typing import Optional

@dataclass(kw_only=True)
class PortfolioCreated(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class PortfolioRenamed(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class PortfolioDeleted(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class HoldingAdded(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    holding_id: UUID
    stock_id: UUID
    quantity: Decimal
    cost_basis: Decimal
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class HoldingRemoved(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    holding_id: UUID
    stock_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class HoldingUpdated(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    holding_id: UUID
    stock_id: UUID
    old_quantity: Optional[Decimal] = None
    new_quantity: Optional[Decimal] = None
    old_cost_basis: Optional[Decimal] = None
    new_cost_basis: Optional[Decimal] = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class ActivityReportEntryAdded(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    activity_entry_id: UUID
    stock_id: Optional[UUID]
    activity_type: str
    amount: Decimal
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class ActivityReportEntryRemoved(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    activity_entry_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class CashBalanceUpdated(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    old_balance: Decimal
    new_balance: Decimal
    reason: str  # e.g., 'deposit', 'withdrawal', 'dividend', 'trade'
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class PortfolioRecalculated(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    recalculation_type: str  # e.g., 'batch_update', 'scenario'
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class PortfolioImported(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    source: str  # e.g., 'IBKR_CSV'
    entries_count: int
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class PortfolioExported(DomainEvent):
    portfolio_id: UUID
    tenant_id: UUID
    export_format: str
    export_purpose: str  # e.g., 'reporting', 'backup'
    occurred_at: datetime = field(default_factory=datetime.utcnow)
