from typing import Optional, List
from uuid import UUID
from domain.user.user import User
from .base import UserRepository

class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users = {}  # Dict[UUID, dict] simulating DB rows
    def get_by_id(self, user_id: UUID, conn=None) -> Optional[User]:
        row = self._users.get(user_id)
        if row:
            return self._row_to_user(row)
        return None
    def get_by_email(self, email: str, conn=None) -> Optional[User]:
        for row in self._users.values():
            if row['email'] == email:
                return self._row_to_user(row)
        return None
    def add(self, user: User, conn=None) -> None:
        self._users[user.id] = self._user_to_row(user)
    def list_by_tenant(self, tenant_id: UUID, conn=None) -> List[User]:
        return [self._row_to_user(row) for row in self._users.values() if row['tenant_id'] == tenant_id]
    def change_password(self, user_id: UUID, new_password_hash: str, conn=None) -> None:
        row = self._users.get(user_id)
        if row:
            row['password_hash'] = new_password_hash

    def _user_to_row(self, user: User) -> dict:
        return {
            'id': user.id,
            'tenant_id': user.tenant_id,
            'email': str(user.email),
            'name': user.name,
            'password_hash': user.password_hash.hashed,
            'role': str(user.role),
            'is_active': user.is_active,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
        }

    def _row_to_user(self, row: dict) -> User:
        from domain.user.user import User, Email, PasswordHash, Role
        return User(
            id=row['id'],
            tenant_id=row['tenant_id'],
            email=Email(row['email']),
            name=row['name'],
            password_hash=PasswordHash(row['password_hash']),
            role=Role(row['role']),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
        )
