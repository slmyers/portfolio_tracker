from typing import Optional, List
from uuid import UUID
from domain.tenant.tenant import Tenant
from .base import TenantRepository
from domain.tenant.tenant import TenantName

class PostgresTenantRepository(TenantRepository):
    def __init__(self, db):
        self.db = db

    def _row_to_tenant(self, row) -> Tenant:
        return Tenant(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            name=TenantName(row["name"]),
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get_by_id(self, tenant_id: UUID, conn=None) -> Optional[Tenant]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tenants WHERE id = %s", (str(tenant_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_tenant(dict(zip(colnames, row)))
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def add(self, tenant: Tenant, conn=None) -> None:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tenants (id, name, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        str(tenant.id),
                        str(tenant.name),
                        tenant.is_active,
                        tenant.created_at,
                        tenant.updated_at
                    )
                )
                if should_close:
                    conn.commit()
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)

    def list_all(self, conn=None) -> List[Tenant]:
        should_close = False
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            should_close = True
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tenants")
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_tenant(dict(zip(colnames, row))) for row in rows]
        finally:
            if should_close:
                conn_ctx.__exit__(None, None, None)
