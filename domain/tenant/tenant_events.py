from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from core.domain_event import DomainEvent

@dataclass(kw_only=True)
class TenantCreated(DomainEvent):
    tenant_id: UUID
    name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class TenantDeactivated(DomainEvent):
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class TenantNameChanged(DomainEvent):
    tenant_id: UUID
    old_name: str
    new_name: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)
