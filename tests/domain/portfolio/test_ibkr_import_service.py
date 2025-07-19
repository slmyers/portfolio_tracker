#!/usr/bin/env python3

import unittest
from uuid import uuid4
from decimal import Decimal

from domain.portfolio.ibkr_import_service import IBKRImportService
from domain.portfolio.holdings_management_service import HoldingsManagementService
from domain.portfolio.activity_management_service import ActivityManagementService
from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from domain.portfolio.models.enums import Currency
from domain.portfolio.models.holding import CashHolding
from tests.repositories.portfolio import InMemoryPortfolioRepository
from tests.repositories.equity import InMemoryEquityRepository
from tests.repositories.holdings import InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository
from tests.repositories.activity_report import InMemoryActivityReportEntryRepository


class IBKRImportServiceTest(unittest.TestCase):
    """Test the specialized IBKRImportService."""

    def setUp(self):
        """Set up test dependencies."""
        self.cash_holding_repo = InMemoryCashHoldingRepository()
        self.portfolio_repo = InMemoryPortfolioRepository(self.cash_holding_repo)
        self.equity_repo = InMemoryEquityRepository()
        self.equity_holding_repo = InMemoryEquityHoldingRepository()
        self.activity_entry_repo = InMemoryActivityReportEntryRepository()
        
        # Create specialized services
        self.holdings_service = HoldingsManagementService(
            self.portfolio_repo, self.equity_repo, 
            self.equity_holding_repo, self.cash_holding_repo
        )
        self.activity_service = ActivityManagementService(
            self.portfolio_repo, self.equity_repo, self.activity_entry_repo
        )
        
        self.service = IBKRImportService(
            portfolio_repo=self.portfolio_repo,
            holdings_service=self.holdings_service,
            activity_service=self.activity_service
        )
        
        self.tenant_id = uuid4()
        
        # Create a test portfolio
        self.portfolio = Portfolio(
            id=uuid4(),
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.portfolio_repo.save(self.portfolio)
        
        # Create initial CAD cash holding
        cash_holding = CashHolding(
            id=uuid4(),
            portfolio_id=self.portfolio.id,
            currency=Currency.CAD,
            balance=Decimal('0')
        )
        self.cash_holding_repo.save(cash_holding)

    def test_import_trades(self):
        """Test importing trades from IBKR data."""
        trades = [
            {
                'symbol': 'AAPL',
                'datetime': '2024-01-01T10:00:00',
                'proceeds': Decimal('1000.00'),
                'quantity': Decimal('10'),
                'commission': Decimal('5.00')
            },
            {
                'symbol': 'GOOGL',
                'datetime': '2024-01-02T11:00:00',
                'proceeds': Decimal('500.00'),
                'quantity': Decimal('5'),
                'commission': Decimal('3.00')
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=trades,
            dividends=[],
            positions=[],
            forex_balances=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.trades_imported, 2)
        self.assertEqual(result.activity_entries_created, 2)
        
        # Verify activity entries were created
        entries = self.activity_service.get_activity_entries(self.portfolio.id, activity_type='TRADE')
        self.assertEqual(len(entries), 2)

    def test_import_dividends(self):
        """Test importing dividends from IBKR data."""
        dividends = [
            {
                'description': 'AAPL Dividend',
                'date': '2024-01-15',
                'amount': Decimal('50.00'),
                'currency': 'USD'
            },
            {
                'description': 'GOOGL Dividend',
                'date': '2024-01-20',
                'amount': Decimal('25.00'),
                'currency': 'CAD'
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=[],
            dividends=dividends,
            positions=[],
            forex_balances=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.dividends_imported, 2)
        self.assertEqual(result.activity_entries_created, 2)
        
        # Verify activity entries were created
        entries = self.activity_service.get_activity_entries(self.portfolio.id, activity_type='DIVIDEND')
        self.assertEqual(len(entries), 2)

    def test_import_positions(self):
        """Test importing positions from IBKR data."""
        positions = [
            {
                'symbol': 'AAPL',
                'quantity': 50,
                'cost_basis': 7525.00
            },
            {
                'symbol': 'GOOGL',
                'quantity': 25,
                'cost_basis': 70000.00
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=[],
            dividends=[],
            positions=positions,
            forex_balances=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.positions_imported, 2)
        self.assertEqual(result.equity_holdings_created, 2)
        self.assertEqual(result.equities_created, 2)
        
        # Verify holdings were created
        holdings = self.holdings_service.get_equity_holdings(self.portfolio.id)
        self.assertEqual(len(holdings), 2)

    def test_import_forex_balances(self):
        """Test importing forex balances from IBKR data."""
        forex_balances = [
            {
                'currency': 'USD',
                'quantity': 37.1525,
                'description': 'USD',
                'asset_category': 'Forex',
                'cost_price': 1.40358455,
                'value_in_cad': 50.82462
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
        self.assertEqual(result.forex_balances_imported, 1)
        self.assertEqual(result.cash_holdings_created, 1)  # USD created, CAD already exists
        
        # Verify cash holdings were updated
        cash_holdings = self.holdings_service.get_cash_holdings(self.portfolio.id)
        self.assertEqual(len(cash_holdings), 2)  # CAD and USD
        
        usd_holding = next((h for h in cash_holdings if h.currency == Currency.USD), None)
        self.assertIsNotNone(usd_holding)
        self.assertEqual(usd_holding.balance, Decimal('37.1525'))

    def test_import_comprehensive_data(self):
        """Test importing comprehensive IBKR data with all types."""
        trades = [
            {
                'symbol': 'AAPL',
                'datetime': '2024-01-01T10:00:00',
                'proceeds': Decimal('1000.00'),
                'quantity': Decimal('10'),
                'commission': Decimal('5.00')
            }
        ]
        
        dividends = [
            {
                'description': 'AAPL Dividend',
                'date': '2024-01-15',
                'amount': Decimal('50.00'),
                'currency': 'USD'
            }
        ]
        
        positions = [
            {
                'symbol': 'AAPL',
                'quantity': 50,
                'cost_basis': 7525.00
            }
        ]
        
        forex_balances = [
            {
                'currency': 'USD',
                'quantity': 1000.00,
                'description': 'USD',
                'asset_category': 'Forex',
                'cost_price': 1.40,
                'value_in_cad': 1400.00
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=trades,
            dividends=dividends,
            positions=positions,
            forex_balances=forex_balances
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.trades_imported, 1)
        self.assertEqual(result.dividends_imported, 1)
        self.assertEqual(result.positions_imported, 1)
        self.assertEqual(result.forex_balances_imported, 1)
        self.assertEqual(result.activity_entries_created, 2)  # 1 trade + 1 dividend
        self.assertEqual(result.equity_holdings_created, 1)
        self.assertEqual(result.cash_holdings_created, 1)

    def test_import_nonexistent_portfolio_fails(self):
        """Test that importing to non-existent portfolio fails gracefully."""
        result = self.service.import_from_ibkr(
            portfolio_id=uuid4(),
            trades=[],
            dividends=[],
            positions=[],
            forex_balances=[]
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "PortfolioNotFoundError")

    def test_import_skips_invalid_trades(self):
        """Test that invalid trades are skipped with warnings."""
        trades = [
            {
                'symbol': 'AAPL',
                'datetime': '2024-01-01T10:00:00',
                'proceeds': Decimal('1000.00')
            },
            {
                # Missing symbol and datetime
                'proceeds': Decimal('500.00'),
                'quantity': Decimal('5')
            }
        ]
        
        result = self.service.import_from_ibkr(
            portfolio_id=self.portfolio.id,
            trades=trades,
            dividends=[],
            positions=[],
            forex_balances=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.trades_imported, 1)
        self.assertEqual(result.skipped_trades, 1)
        self.assertEqual(len(result.warnings), 1)

    def test_import_skips_unsupported_currency(self):
        """Test that unsupported currencies are skipped with warnings."""
        forex_balances = [
            {
                'currency': 'CHF',  # Not supported in Currency enum
                'quantity': 100.00,
                'description': 'CHF',
                'asset_category': 'Forex'
            },
            {
                'currency': 'USD',
                'quantity': 37.1525,
                'description': 'USD',
                'asset_category': 'Forex'
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
        self.assertEqual(result.forex_balances_imported, 1)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Unsupported currency 'CHF'", result.warnings[0])


if __name__ == '__main__':
    unittest.main()
