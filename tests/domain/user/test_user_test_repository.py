import unittest
from uuid import uuid4
from passlib.context import CryptContext
from domain.user.user import User, Email, PasswordHash, Role
from tests.repositories.user import InMemoryUserRepository

class UserTestRepositoryTest(unittest.TestCase):
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


    def test_change_password(self):
        user = self.repo.get_by_id(self.user_id)
        old_hash = user.password_hash.hashed
        new_hash = "newhashvalue123"
        self.repo.change_password(self.user_id, new_hash)
        user = self.repo.get_by_id(self.user_id)
        self.assertEqual(user.password_hash.hashed, new_hash)
        self.assertNotEqual(user.password_hash.hashed, old_hash)

if __name__ == "__main__":
    unittest.main()
