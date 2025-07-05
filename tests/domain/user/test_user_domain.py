import unittest
from uuid import uuid4
from datetime import datetime
from domain.user.user import User, Email, PasswordHash, Role
from domain.user.user_events import UserAdded, UserRemoved, UserRoleChanged
from passlib.context import CryptContext

class UserDomainTestCase(unittest.TestCase):
    def setUp(self):
        self.user_id = uuid4()
        self.tenant_id = uuid4()
        self.email = Email("user@example.com")
        self.name = "Test User"
        self.password_hash = PasswordHash("hashedpw")
        self.role = Role("user")
        self.user = User(
            id=self.user_id,
            tenant_id=self.tenant_id,
            email=self.email,
            name=self.name,
            password_hash=self.password_hash,
            role=self.role
        )

    def test_password_hash_create_and_verify(self):
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        password = "supersecret"
        hash_obj = PasswordHash.create(password, pwd_context)
        self.assertTrue(hash_obj.verify(password, pwd_context))
        self.assertFalse(hash_obj.verify("wrongpassword", pwd_context))

    def test_password_hash_direct_init_and_verify(self):
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        password = "anothersecret"
        hash_obj = PasswordHash.create(password, pwd_context)
        # Simulate loading from DB
        loaded_hash = PasswordHash(hash_obj.hashed)
        self.assertTrue(loaded_hash.verify(password, pwd_context))
        self.assertFalse(loaded_hash.verify("bad", pwd_context))

    def test_user_added_event(self):
        events = self.user.pull_events()
        self.assertTrue(any(isinstance(e, UserAdded) for e in events))

    def test_deactivate_records_event(self):
        self.user.deactivate()
        events = self.user.pull_events()
        self.assertTrue(any(isinstance(e, UserRemoved) for e in events))
        self.assertFalse(self.user.is_active)

    def test_change_role_records_event(self):
        new_role = Role("admin")
        self.user.change_role(new_role, changed_by="admin_id")
        events = self.user.pull_events()
        self.assertTrue(any(isinstance(e, UserRoleChanged) for e in events))
        self.assertEqual(str(self.user.role), "admin")

if __name__ == "__main__":
    unittest.main()
