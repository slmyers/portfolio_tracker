from typing import Optional, List
from uuid import UUID
from domain.user.user import User
from .base import UserRepository

class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users = {}
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self._users.get(user_id)
    def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if str(user.email) == email:
                return user
        return None
    def add(self, user: User) -> None:
        self._users[user.id] = user
    def list_by_tenant(self, tenant_id: UUID) -> List[User]:
        return [u for u in self._users.values() if u.tenant_id == tenant_id]
