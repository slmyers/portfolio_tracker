import unittest
from uuid import uuid4
from passlib.context import CryptContext
from domain.user.user import User, Email, PasswordHash, Role
from domain.user.repository.postgres import PostgresUserRepository
from domain.tenant.tenant import Tenant, TenantName
from domain.tenant.repository.postgres import PostgresTenantRepository
from core.persistence.postgres import PostgresPool
from core.config.config import get_test_postgres_config

class PostgresUserRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = get_test_postgres_config()
        cls.db = PostgresPool(cls.config)
        cls.tenant_repo = PostgresTenantRepository(cls.db)
        cls.repo = PostgresUserRepository(cls.db)
        cls.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def setUp(self):
        self.conn_ctx = self.db.connection()
        self.conn, _ = self.conn_ctx.__enter__()
        self.conn.autocommit = False
        self.user_id = uuid4()
        self.tenant_id = uuid4()
        self.tenant = Tenant(
            id=self.tenant_id,
            name=TenantName("Test Tenant")
        )
        self.tenant_repo.add(self.tenant, conn=self.conn)
        self.user = User(
            id=self.user_id,
            tenant_id=self.tenant_id,
            email=Email("test@example.com"),
            name="Test User",
            password_hash=PasswordHash.create("password", self.pwd_context),
            role=Role("user")
        )
        self.repo.add(self.user, conn=self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn_ctx.__exit__(None, None, None)

    def test_get_by_id(self):
        user = self.repo.get_by_id(self.user_id, conn=self.conn)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user_id)

    def test_get_by_email(self):
        user = self.repo.get_by_email("test@example.com", conn=self.conn)
        self.assertIsNotNone(user)
        self.assertEqual(str(user.email), "test@example.com")

    def test_list_by_tenant(self):
        users = self.repo.list_by_tenant(self.tenant_id, conn=self.conn)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].tenant_id, self.tenant_id)

    def test_change_password(self):
        user = self.repo.get_by_id(self.user_id, conn=self.conn)
        old_hash = user.password_hash
        new_hash = "newhashvalue123"
        self.repo.change_password(self.user_id, new_hash, conn=self.conn)
        user = self.repo.get_by_id(self.user_id, conn=self.conn)
        self.assertEqual(user.password_hash.hashed, new_hash)
        self.assertNotEqual(user.password_hash.hashed, old_hash.hashed)

if __name__ == "__main__":
    unittest.main()
