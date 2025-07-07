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
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tenants WHERE id = %s", (str(tenant_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_tenant(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def add(self, tenant: Tenant, conn=None) -> None:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
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
                # Only commit if we created our own connection
                if conn_ctx is not None:
                    conn.commit()
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def list_all(self, conn=None) -> List[Tenant]:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tenants")
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_tenant(dict(zip(colnames, row))) for row in rows]
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)
