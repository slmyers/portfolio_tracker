#!/usr/bin/env python3

import unittest
from uuid import uuid4
from decimal import Decimal

from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.repository.in_memory import (
    InMemoryPortfolioRepository, InMemoryEquityRepository, 
    InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository,
    InMemoryActivityReportEntryRepository
)


class ForexBalancesImportTest(unittest.TestCase):
    """Test importing forex balances from IBKR CSV."""

    def setUp(self):
        """Set up test dependencies."""
        self.portfolio_repo = InMemoryPortfolioRepository()
        self.equity_repo = InMemoryEquityRepository()
        self.equity_holding_repo = InMemoryEquityHoldingRepository()
        self.cash_holding_repo = InMemoryCashHoldingRepository()
        self.activity_entry_repo = InMemoryActivityReportEntryRepository()
        
        self.service = PortfolioService(
            portfolio_repo=self.portfolio_repo,
            equity_repo=self.equity_repo,
            equity_holding_repo=self.equity_holding_repo,
            cash_holding_repo=self.cash_holding_repo,
            activity_entry_repo=self.activity_entry_repo
        )
        
        self.tenant_id = uuid4()
        
        # Create a test portfolio
        self.portfolio = self.service.create_portfolio(
            tenant_id=self.tenant_id,
            name="Test Portfolio"
        )

    def test_forex_balances_import_creates_cash_holdings(self):
        """Test that forex balances are correctly imported as cash holdings."""
        # Sample forex balances data (matching our parser output)
        forex_balances = [
            {
                'currency': 'CAD',
                'quantity': 72.611174145,
                'description': 'CAD',
                'asset_category': 'Forex',
                'cost_price': 0.0,
                'value_in_cad': 72.611174145
            },
            {
                'currency': 'USD',
                'quantity': 37.1525,
                'description': 'USD', 
                'asset_category': 'Forex',
                'cost_price': 1.40358455,
                'value_in_cad': 50.82462
            }
        ]
        
        # Import the forex balances
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=[],
            dividends=[],
            positions=[],
            forex_balances=forex_balances
        )
        
        # Verify import was successful
        self.assertTrue(result.success)
        self.assertEqual(result.forex_balances_imported, 2)
        
        # Debug: print initial cash holdings
        initial_holdings = self.service.get_cash_holdings(self.portfolio.id)
        print(f"Initial holdings: {[(h.currency.value, h.balance) for h in initial_holdings]}")
        print(f"Cash holdings created: {result.cash_holdings_created}")
        
        # USD should be created (new), CAD should be updated (existing)
        self.assertEqual(result.cash_holdings_created, 1)
        
        # Verify cash holdings were created correctly
        cash_holdings = self.service.get_cash_holdings(self.portfolio.id)
        self.assertEqual(len(cash_holdings), 2)
        
        # Check CAD balance (should be updated from initial 0 to forex balance)
        cad_holding = next((h for h in cash_holdings if h.currency.value == 'CAD'), None)
        self.assertIsNotNone(cad_holding)
        self.assertEqual(cad_holding.balance, Decimal('72.611174145'))
        
        # Check USD balance
        usd_holding = next((h for h in cash_holdings if h.currency.value == 'USD'), None)
        self.assertIsNotNone(usd_holding)
        self.assertEqual(usd_holding.balance, Decimal('37.1525'))

    def test_forex_balances_handles_unsupported_currency(self):
        """Test that unsupported currencies are skipped with warnings."""
        forex_balances = [
            {
                'currency': 'BTC',  # Not supported in our Currency enum
                'quantity': 100.0,
                'description': 'BTC'
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=[],
            dividends=[],
            positions=[],
            forex_balances=forex_balances
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.forex_balances_imported, 0)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Unsupported currency 'BTC'", result.warnings[0])

    def test_forex_balances_handles_missing_data(self):
        """Test that forex balances with missing data are skipped."""
        forex_balances = [
            {
                'currency': None,  # Missing currency
                'quantity': 100.0
            },
            {
                'currency': 'USD',
                'quantity': None  # Missing quantity
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=[],
            dividends=[],
            positions=[],
            forex_balances=forex_balances
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.forex_balances_imported, 0)
        self.assertEqual(len(result.warnings), 2)


if __name__ == '__main__':
    unittest.main()
