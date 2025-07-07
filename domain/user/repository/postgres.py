from typing import Optional, List
from uuid import UUID
from domain.user.user import User
from .base import UserRepository
from domain.user.user import Email, PasswordHash, Role
from datetime import datetime

class PostgresUserRepository(UserRepository):
    def __init__(self, db):
        self.db = db  # db should be a connection/session object or pool

    def _hydrate_user(self, id: UUID, tenant_id: UUID, email: Email, name: str, password_hash: PasswordHash, role: Role, is_active: bool, created_at: datetime, updated_at: datetime) -> User:
        # Create a User object without triggering events
        user = User.__new__(User)  # Bypass the constructor
        user.id = id
        user.tenant_id = tenant_id
        user.email = email
        user.name = name
        user.password_hash = password_hash
        user.role = role
        user.is_active = is_active
        user.created_at = created_at
        user.updated_at = updated_at
        return user

    def _row_to_user(self, row) -> User:
        return self._hydrate_user(
            id=UUID(row["id"]) if not isinstance(row["id"], UUID) else row["id"],
            tenant_id=UUID(row["tenant_id"]) if not isinstance(row["tenant_id"], UUID) else row["tenant_id"],
            email=Email(row["email"]),
            name=row["name"],
            password_hash=PasswordHash(row["password_hash"]),
            role=Role(row["role"]),
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def get_by_id(self, user_id: UUID, conn=None) -> Optional[User]:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM users WHERE id = %s
                """, (str(user_id),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_user(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def get_by_email(self, email: str, conn=None) -> Optional[User]:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM users WHERE email = %s
                """, (email.lower(),))
                row = cur.fetchone()
                if not row:
                    return None
                colnames = [desc[0] for desc in cur.description]
                return self._row_to_user(dict(zip(colnames, row)))
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def add(self, user: User, conn=None) -> None:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (id, tenant_id, email, name, password_hash, role, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """,
                (
                    str(user.id),
                    str(user.tenant_id),
                    str(user.email),
                    user.name,
                    user.password_hash.hashed,
                    str(user.role),
                    user.is_active,
                    user.created_at,
                    user.updated_at
                ))
                if conn_ctx is not None:
                    conn.commit()
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def list_by_tenant(self, tenant_id: UUID, conn=None) -> List[User]:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM users WHERE tenant_id = %s
                """, (str(tenant_id),))
                rows = cur.fetchall()
                colnames = [desc[0] for desc in cur.description]
                return [self._row_to_user(dict(zip(colnames, row))) for row in rows]
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)

    def change_password(self, user_id: UUID, new_password_hash: str, conn=None) -> None:
        conn_ctx = None
        if conn is None:
            conn_ctx = self.db.connection()
            conn, _ = conn_ctx.__enter__()
            
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users SET password_hash = %s, updated_at = %s WHERE id = %s
                """, (new_password_hash, datetime.utcnow(), str(user_id)))
                if conn_ctx is not None:
                    conn.commit()
        finally:
            if conn_ctx is not None:
                conn_ctx.__exit__(None, None, None)
