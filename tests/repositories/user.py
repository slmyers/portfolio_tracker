"""Test-specific in-memory user repository with mocking and assertion utilities."""

from typing import Optional, List, Dict
from uuid import UUID, uuid4
from datetime import datetime
from passlib.context import CryptContext

from domain.user.user import User, Email, PasswordHash, Role


class TestUserRepository:
    """Test-specific in-memory implementation of UserRepository with utilities for testing."""
    
    def __init__(self):
        self._users: Dict[UUID, User] = {}
        self._call_history: List[dict] = []

    def add(self, user: User, conn=None) -> None:
        self._record_call('add', {'user_id': user.id})
        self._users[user.id] = user

    def get_by_id(self, user_id: UUID, conn=None) -> Optional[User]:
        self._record_call('get_by_id', {'user_id': user_id})
        return self._users.get(user_id)

    def get_by_email(self, email: str, conn=None) -> Optional[User]:
        self._record_call('get_by_email', {'email': email})
        for user in self._users.values():
            if str(user.email) == email:
                return user
        return None

    def update(self, user: User, conn=None) -> None:
        self._record_call('update', {'user_id': user.id})
        if user.id in self._users:
            self._users[user.id] = user

    def delete(self, user_id: UUID, conn=None) -> None:
        self._record_call('delete', {'user_id': user_id})
        self._users.pop(user_id, None)

    def exists(self, user_id: UUID, conn=None) -> bool:
        self._record_call('exists', {'user_id': user_id})
        return user_id in self._users

    def change_password(self, user_id: UUID, new_password_hash: str, conn=None) -> None:
        self._record_call('change_password', {'user_id': user_id})
        user = self._users.get(user_id)
        if user:
            # Create a new PasswordHash object with the new hash
            user.password_hash = PasswordHash(new_password_hash)
            self._users[user_id] = user

    def list_by_tenant(self, tenant_id: UUID, conn=None) -> List[User]:
        self._record_call('list_by_tenant', {'tenant_id': tenant_id})
        return [user for user in self._users.values() if user.tenant_id == tenant_id]

    def _record_call(self, method: str, args: dict):
        """Record method calls for testing assertions."""
        self._call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now()
        })

    # Test utility methods
    def mock_user(
        self, 
        user_id: UUID = None,
        tenant_id: UUID = None,
        email: str = "test@example.com",
        name: str = "Test User",
        password: str = "password",
        role: str = "user",
        pwd_context: CryptContext = None
    ) -> User:
        """Create and save a mock user for testing."""
        user_id = user_id or uuid4()
        tenant_id = tenant_id or uuid4()
        pwd_context = pwd_context or CryptContext(schemes=["argon2"], deprecated="auto")
        
        user = User(
            id=user_id,
            tenant_id=tenant_id,
            email=Email(email),
            name=name,
            password_hash=PasswordHash.create(password, pwd_context),
            role=Role(role)
        )
        
        self.add(user)
        return user

    def assert_user_exists(self, user_id: UUID) -> bool:
        """Assert that a user exists in the repository."""
        return self.exists(user_id)

    def assert_user_by_email_exists(self, email: str) -> bool:
        """Assert that a user with given email exists."""
        user = self.get_by_email(email)
        return user is not None

    def assert_method_called(self, method_name: str, times: int = None) -> bool:
        """Assert that a method was called a specific number of times."""
        calls = [call for call in self._call_history if call['method'] == method_name]
        if times is None:
            return len(calls) > 0
        return len(calls) == times

    def get_call_history(self) -> List[dict]:
        """Get the history of method calls for testing."""
        return self._call_history

    def clear_call_history(self):
        """Clear the call history for testing."""
        self._call_history = []

    def clear_data(self):
        """Clear all user data for testing."""
        self._users.clear()
        self.clear_call_history()

    def get_user_count(self) -> int:
        """Get the total number of users in the repository."""
        return len(self._users)
