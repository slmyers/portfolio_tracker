from typing import Optional, List
from uuid import UUID
from domain.user.user import User
from domain.user.repository.base import UserRepository
from domain.user.user import PasswordHash
from passlib.context import CryptContext

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user_by_id(self, user_id: UUID, conn=None) -> Optional[User]:
        return self.user_repo.get_by_id(user_id, conn=conn)

    def get_user_by_email(self, email: str, conn=None) -> Optional[User]:
        return self.user_repo.get_by_email(email, conn=conn)

    def add_user(self, user: User, conn=None) -> None:
        self.user_repo.add(user, conn=conn)

    def list_users_by_tenant(self, tenant_id: UUID, conn=None) -> List[User]:
        return self.user_repo.list_by_tenant(tenant_id, conn=conn)

    def change_user_password(self, user_id: UUID, new_password: str, conn=None) -> None:
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        new_hash = PasswordHash.create(new_password, pwd_context).hashed
        self.user_repo.change_password(user_id, new_hash, conn=conn)

    def verify_user_password(self, user_id: UUID, plain_password: str, conn=None) -> tuple[bool, str]:
        """
        Verifies a plain password against the stored hash for the user with the given ID.
        Returns (True, "match") if the password matches,
        (False, reason) otherwise.
        """
        user = self.get_user_by_id(user_id, conn=conn)
        if not user:
            return False, "user_not_found"
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        try:
            if user.password_hash.verify(plain_password, pwd_context):
                return True, "match"
            else:
                return False, "password_mismatch"
        except Exception as e:
            return False, f"error: {str(e)}"
