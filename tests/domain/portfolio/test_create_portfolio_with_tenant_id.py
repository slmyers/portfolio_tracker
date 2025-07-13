"""
Test for Issue 3: Creating portfolio with separate tenant_id and portfolio_id
"""
import unittest
from uuid import uuid4
from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.repository.in_memory import (
    InMemoryPortfolioRepository,
    InMemoryEquityRepository, 
    InMemoryEquityHoldingRepository,
    InMemoryCashHoldingRepository,
    InMemoryActivityReportEntryRepository
)


class TestCreatePortfolioWithTenantId(unittest.TestCase):
    def setUp(self):
        self.equity_repo = InMemoryEquityRepository()
        self.equity_holding_repo = InMemoryEquityHoldingRepository()
        self.cash_holding_repo = InMemoryCashHoldingRepository()
        self.portfolio_repo = InMemoryPortfolioRepository(self.cash_holding_repo)
        self.activity_repo = InMemoryActivityReportEntryRepository()
        
        self.service = PortfolioService(
            self.portfolio_repo,
            self.equity_repo,
            self.equity_holding_repo,
            self.cash_holding_repo,
            self.activity_repo
        )

    def test_create_portfolio_with_tenant_id(self):
        """Test that portfolio creation correctly distinguishes between tenant_id and portfolio_id."""
        tenant_id = uuid4()
        portfolio_id = uuid4()
        
        # Create portfolio with specific portfolio_id and tenant_id
        portfolio = self.service.create_portfolio(
            tenant_id=tenant_id, 
            name="Test Portfolio", 
            portfolio_id=portfolio_id
        )
        
        # Verify correct assignment
        self.assertEqual(portfolio.tenant_id, tenant_id)
        self.assertEqual(portfolio.id, portfolio_id)
        self.assertNotEqual(portfolio.tenant_id, portfolio.id)  # They should be different
        
        # Verify the portfolio is saved correctly
        retrieved = self.service.get_portfolio(portfolio_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.tenant_id, tenant_id)
        self.assertEqual(retrieved.id, portfolio_id)

    def test_create_portfolio_without_explicit_portfolio_id(self):
        """Test that portfolio creation still works when portfolio_id is not explicitly provided."""
        tenant_id = uuid4()
        
        # Create portfolio without specifying portfolio_id (should auto-generate)
        portfolio = self.service.create_portfolio(
            tenant_id=tenant_id, 
            name="Test Portfolio"
        )
        
        # Verify correct assignment
        self.assertEqual(portfolio.tenant_id, tenant_id)
        self.assertIsNotNone(portfolio.id)
        self.assertNotEqual(portfolio.tenant_id, portfolio.id)  # They should be different

    def test_create_multiple_portfolios_same_tenant(self):
        """Test creating multiple portfolios for the same tenant."""
        tenant_id = uuid4()
        portfolio_id_1 = uuid4()
        portfolio_id_2 = uuid4()
        
        # Create two portfolios for the same tenant
        portfolio1 = self.service.create_portfolio(
            tenant_id=tenant_id, 
            name="Portfolio 1", 
            portfolio_id=portfolio_id_1
        )
        
        portfolio2 = self.service.create_portfolio(
            tenant_id=tenant_id, 
            name="Portfolio 2", 
            portfolio_id=portfolio_id_2
        )
        
        # Both should belong to the same tenant but have different IDs
        self.assertEqual(portfolio1.tenant_id, tenant_id)
        self.assertEqual(portfolio2.tenant_id, tenant_id)
        self.assertEqual(portfolio1.id, portfolio_id_1)
        self.assertEqual(portfolio2.id, portfolio_id_2)
        self.assertNotEqual(portfolio1.id, portfolio2.id)
        
        # Verify they can be retrieved
        all_portfolios = self.service.get_portfolios_by_tenant(tenant_id)
        self.assertEqual(len(all_portfolios), 2)


if __name__ == '__main__':
    unittest.main()
