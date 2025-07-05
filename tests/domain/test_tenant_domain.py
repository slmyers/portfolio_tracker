import unittest
from uuid import uuid4
from datetime import datetime
from domain.tenant.tenant import Tenant, TenantName
from domain.tenant.events import TenantDeactivated, TenantCreated, TenantNameChanged

class TenantDomainTestCase(unittest.TestCase):
    def setUp(self):
        self.tenant_id = uuid4()
        self.name = TenantName("Test Tenant")
        self.tenant = Tenant(id=self.tenant_id, name=self.name)

    def test_deactivate_records_event(self):
        self.tenant.deactivate()
        events = self.tenant.pull_events()
        self.assertTrue(any(isinstance(e, TenantDeactivated) for e in events))
        self.assertFalse(self.tenant.is_active)

    def test_activate_records_event(self):
        self.tenant.is_active = False
        self.tenant.activate()
        events = self.tenant.pull_events()
        self.assertTrue(any(isinstance(e, TenantCreated) for e in events))
        self.assertTrue(self.tenant.is_active)

    def test_change_name_records_event(self):
        new_name = TenantName("New Name")
        self.tenant.change_name(new_name)
        events = self.tenant.pull_events()
        self.assertTrue(any(isinstance(e, TenantNameChanged) for e in events))
        self.assertEqual(str(self.tenant.name), "New Name")

if __name__ == "__main__":
    unittest.main()
