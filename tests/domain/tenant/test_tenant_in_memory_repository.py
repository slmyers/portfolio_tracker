import unittest
from uuid import uuid4
from domain.tenant.tenant import Tenant, TenantName
from domain.tenant.repository.in_memory import InMemoryTenantRepository

class InMemoryTenantRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryTenantRepository()
        self.tenant_id = uuid4()
        self.tenant = Tenant(
            id=self.tenant_id,
            name=TenantName("Test Tenant")
        )
        self.repo.add(self.tenant)

    def test_get_by_id(self):
        tenant = self.repo.get_by_id(self.tenant_id)
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.id, self.tenant_id)

    def test_list_all(self):
        tenants = self.repo.list_all()
        self.assertEqual(len(tenants), 1)
        self.assertEqual(tenants[0].id, self.tenant_id)

    def test_add_duplicate_id_overwrites(self):
        # Adding a tenant with the same id should overwrite
        tenant2 = Tenant(
            id=self.tenant_id,
            name=TenantName("Other Tenant")
        )
        self.repo.add(tenant2)
        tenant = self.repo.get_by_id(self.tenant_id)
        self.assertEqual(tenant.name, TenantName("Other Tenant"))

if __name__ == "__main__":
    unittest.main()
