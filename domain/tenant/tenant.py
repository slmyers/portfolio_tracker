from uuid import UUID
from datetime import datetime
from core.domain_model import DomainModel
from .tenant_events import TenantDeactivated, TenantCreated, TenantNameChanged
from typing import Optional

class TenantName:
    MAX_LENGTH = 100
    def __init__(self, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Tenant name cannot be empty")
        if len(value) > self.MAX_LENGTH:
            raise ValueError(f"Tenant name must be at most {self.MAX_LENGTH} characters")
        self.value = value
    def __str__(self):
        return self.value
    def __eq__(self, other):
        return isinstance(other, TenantName) and self.value == other.value

class Tenant(DomainModel):
    def __init__(self, id: UUID, name: TenantName, is_active: bool = True, created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        super().__init__()
        self.id = id
        self.name = name
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
    def deactivate(self):
        if not self.is_active:
            return
        self.is_active = False
        self.updated_at = datetime.utcnow()
        self.record_event(TenantDeactivated(
            tenant_id=self.id,
            occurred_at=self.updated_at
        ))
    def activate(self):
        if self.is_active:
            return
        self.is_active = True
        self.updated_at = datetime.utcnow()
        self.record_event(TenantCreated(
            tenant_id=self.id,
            name=str(self.name),
            occurred_at=self.updated_at
        ))
    def change_name(self, new_name: TenantName):
        if self.name == new_name:
            return
        old_name = str(self.name)
        self.name = new_name
        self.updated_at = datetime.utcnow()
        self.record_event(TenantNameChanged(
            tenant_id=self.id,
            old_name=old_name,
            new_name=str(new_name),
            occurred_at=self.updated_at
        ))
