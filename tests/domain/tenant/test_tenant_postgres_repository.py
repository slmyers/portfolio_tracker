import unittest
from uuid import uuid4
from domain.tenant.tenant import Tenant, TenantName
from domain.tenant.repository.postgres import PostgresTenantRepository
from core.persistence.postgres import PostgresPool
from core.config.config import get_test_postgres_config

class PostgresTenantRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = get_test_postgres_config()
        cls.db = PostgresPool(cls.config)
        cls.repo = PostgresTenantRepository(cls.db)

    def setUp(self):
        self.conn_ctx = self.db.connection()
        self.conn, _ = self.conn_ctx.__enter__()
        self.conn.autocommit = False
        self.tenant_id = uuid4()
        self.tenant = Tenant(
            id=self.tenant_id,
            name=TenantName("Test Tenant")
        )
        self.repo.add(self.tenant, conn=self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn_ctx.__exit__(None, None, None)

    def test_get_by_id(self):
        tenant = self.repo.get_by_id(self.tenant_id, conn=self.conn)
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.id, self.tenant_id)
        self.assertEqual(str(tenant.name), "Test Tenant")

    def test_list_all(self):
        tenants = self.repo.list_all(conn=self.conn)
        self.assertTrue(any(t.id == self.tenant_id for t in tenants))

if __name__ == "__main__":
    unittest.main()
