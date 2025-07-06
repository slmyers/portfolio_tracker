import unittest
from uuid import uuid4
from passlib.context import CryptContext
from domain.user.user import User, Email, PasswordHash, Role
from domain.user.repository.in_memory import InMemoryUserRepository
from domain.user.user_service import UserService

class UserServiceTest(unittest.TestCase):
    def setUp(self):
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        self.repo = InMemoryUserRepository()
        self.service = UserService(self.repo)
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
        self.service.add_user(self.user)

    def test_get_user_by_id(self):
        user = self.service.get_user_by_id(self.user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user_id)

    def test_get_user_by_email(self):
        user = self.service.get_user_by_email("test@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(str(user.email), "test@example.com")

    def test_list_users_by_tenant(self):
        users = self.service.list_users_by_tenant(self.tenant_id)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tenant_id, self.tenant_id)

    def test_change_user_password(self):
        user = self.service.get_user_by_id(self.user_id)
        old_hash = user.password_hash.hashed
        new_password = "newpassword123"
        self.service.change_user_password(self.user_id, new_password)
        user = self.service.get_user_by_id(self.user_id)
        self.assertNotEqual(user.password_hash.hashed, old_hash)
        self.assertTrue(self.pwd_context.verify(new_password, user.password_hash.hashed))

    def test_verify_user_password(self):
        # Correct password
        ok, reason = self.service.verify_user_password(self.user_id, "password")
        self.assertTrue(ok)
        self.assertEqual(reason, "match")
        # Incorrect password
        ok, reason = self.service.verify_user_password(self.user_id, "wrongpassword")
        self.assertFalse(ok)
        self.assertEqual(reason, "password_mismatch")
        # Nonexistent user
        ok, reason = self.service.verify_user_password(uuid4(), "password")
        self.assertFalse(ok)
        self.assertEqual(reason, "user_not_found")

if __name__ == "__main__":
    unittest.main()
