from typing import Optional, List
from uuid import UUID
from domain.tenant.tenant import Tenant
from .base import TenantRepository

class PostgresTenantRepository(TenantRepository):
    def __init__(self, db):
        self.db = db  # db should be a connection/session object
    def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        # Implement actual SQL query here
        raise NotImplementedError
    def add(self, tenant: Tenant) -> None:
        # Implement actual SQL insert here
        raise NotImplementedError
    def list_all(self) -> List[Tenant]:
        # Implement actual SQL query here
        raise NotImplementedError
