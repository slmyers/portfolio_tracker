import unittest
from uuid import uuid4
from passlib.context import CryptContext
from domain.user.user import User, Email, PasswordHash, Role
from domain.user.repository.in_memory import InMemoryUserRepository

class InMemoryUserRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self.repo = InMemoryUserRepository()
        self.user_id = uuid4()
        self.tenant_id = uuid4()
        self.user = User(
            id=self.user_id,
            tenant_id=self.tenant_id,
            email=Email("test@example.com"),
            name="Test User",
            password_hash=PasswordHash.create("password", self.pwd_context),
            role=Role("user")
        )
        self.repo.add(self.user)

    def test_get_by_id(self):
        user = self.repo.get_by_id(self.user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user_id)

    def test_get_by_email(self):
        user = self.repo.get_by_email("test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(str(user.email), "test@example.com")

    def test_list_by_tenant(self):
        users = self.repo.list_by_tenant(self.tenant_id)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tenant_id, self.tenant_id)

    def test_add_duplicate_id_overwrites(self):
        # Adding a user with the same id should overwrite
        user2 = User(
            id=self.user_id,
            tenant_id=self.tenant_id,
            email=Email("other@example.com"),
            name="Other User",
            password_hash=PasswordHash.create("password2", self.pwd_context),
            role=Role("admin")
        )
        self.repo.add(user2)
        user = self.repo.get_by_id(self.user_id)
        self.assertEqual(str(user.email), "other@example.com")

if __name__ == "__main__":
    unittest.main()
