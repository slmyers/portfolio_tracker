from typing import Optional, List
from uuid import UUID
from domain.tenant.tenant import Tenant
from .base import TenantRepository

class InMemoryTenantRepository(TenantRepository):
    def __init__(self):
        self._tenants = {}
    def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)
    def add(self, tenant: Tenant) -> None:
        self._tenants[tenant.id] = tenant
    def list_all(self) -> List[Tenant]:
        return list(self._tenants.values())
