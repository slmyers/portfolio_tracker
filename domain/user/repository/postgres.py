from typing import Optional, List
from uuid import UUID
from domain.user.user import User
from .base import UserRepository

class PostgresUserRepository(UserRepository):
    def __init__(self, db):
        self.db = db  # db should be a connection/session object
    def get_by_id(self, user_id: UUID) -> Optional[User]:
        # Implement actual SQL query here
        raise NotImplementedError
    def get_by_email(self, email: str) -> Optional[User]:
        # Implement actual SQL query here
        raise NotImplementedError
    def add(self, user: User) -> None:
        # Implement actual SQL insert here
        raise NotImplementedError
    def list_by_tenant(self, tenant_id: UUID) -> List[User]:
        # Implement actual SQL query here
        raise NotImplementedError
