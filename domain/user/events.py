from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from core.domain_event import DomainEvent

@dataclass(kw_only=True)
class UserAdded(DomainEvent):
    user_id: UUID
    tenant_id: UUID
    email: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class UserRemoved(DomainEvent):
    user_id: UUID
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=datetime.utcnow)

@dataclass(kw_only=True)
class UserRoleChanged(DomainEvent):
    user_id: UUID
    tenant_id: UUID
    old_role: str
    new_role: str
    changed_by: str | None = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)
