import unittest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.repository.in_memory import (
    InMemoryPortfolioRepository, InMemoryEquityRepository,
    InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository,
    InMemoryActivityReportEntryRepository
)
from domain.portfolio.portfolio_errors import DuplicateHoldingError

class PortfolioServiceTest(unittest.TestCase):
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
        
        self.tenant_id = uuid4()

    def test_create_portfolio(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "My Portfolio")
        
        self.assertIsNotNone(portfolio)
        self.assertEqual(str(portfolio.name), "My Portfolio")
        self.assertEqual(portfolio.tenant_id, self.tenant_id)
        self.assertEqual(portfolio.cash_balance, Decimal('0'))
        
        # Verify it's saved in repository
        saved_portfolio = self.portfolio_repo.get(portfolio.id)
        self.assertIsNotNone(saved_portfolio)

    def test_get_portfolio(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        retrieved = self.service.get_portfolio(portfolio.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, portfolio.id)

    def test_get_nonexistent_portfolio(self):
        retrieved = self.service.get_portfolio(uuid4())
        self.assertIsNone(retrieved)

    def test_rename_portfolio(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Original Name")
        
        success = self.service.rename_portfolio(portfolio.id, "New Name")
        self.assertTrue(success)
        
        updated = self.service.get_portfolio(portfolio.id)
        self.assertEqual(str(updated.name), "New Name")

    def test_rename_nonexistent_portfolio(self):
        success = self.service.rename_portfolio(uuid4(), "New Name")
        self.assertFalse(success)

    def test_add_holding_new_stock(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        holding = self.service.add_equity_holding(
            portfolio.id, 
            "AAPL", 
            Decimal('100'), 
            Decimal('1000.00')
        )
        
        self.assertIsNotNone(holding)
        self.assertEqual(holding.quantity, Decimal('100'))
        self.assertEqual(holding.cost_basis, Decimal('1000.00'))
        
        # Verify stock was created
        stock = self.equity_repo.find_by_symbol("AAPL", "NASDAQ")
        self.assertIsNotNone(stock)
        self.assertEqual(stock.symbol, "AAPL")
        
        # Verify holding was saved
        saved_holding = self.equity_holding_repo.get(holding.id)
        self.assertIsNotNone(saved_holding)

    def test_add_holding_existing_stock(self):
        # First create a stock
        portfolio1 = self.service.create_portfolio(self.tenant_id, "Portfolio 1")
        self.service.add_equity_holding(portfolio1.id, "AAPL", Decimal('50'), Decimal('500.00'))
        
        # Now add holding for same stock in different portfolio
        portfolio2 = self.service.create_portfolio(self.tenant_id, "Portfolio 2")
        holding = self.service.add_equity_holding(
            portfolio2.id, 
            "AAPL", 
            Decimal('75'), 
            Decimal('750.00')
        )
        
        self.assertIsNotNone(holding)
        
        # Verify only one stock exists
        all_holdings = self.equity_holding_repo.find_by_portfolio_id(portfolio1.id) + \
                      self.equity_holding_repo.find_by_portfolio_id(portfolio2.id)
        stock_ids = {h.equity_id for h in all_holdings}
        self.assertEqual(len(stock_ids), 1)  # Same stock used

    def test_add_duplicate_holding_raises_error(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        # Add first holding
        self.service.add_equity_holding(portfolio.id, "AAPL", Decimal('100'), Decimal('1000.00'))
        
        # Try to add another holding for same stock
        with self.assertRaises(DuplicateHoldingError):
            self.service.add_equity_holding(portfolio.id, "AAPL", Decimal('50'), Decimal('500.00'))

    def test_add_holding_nonexistent_portfolio(self):
        holding = self.service.add_equity_holding(
            uuid4(),  # Nonexistent portfolio
            "AAPL", 
            Decimal('100'), 
            Decimal('1000.00')
        )
        self.assertIsNone(holding)

    def test_update_cash_balance(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        success = self.service.update_cash_balance(
            portfolio.id, 
            Decimal('500.00'), 
            'deposit'
        )
        self.assertTrue(success)
        
        updated = self.service.get_portfolio(portfolio.id)
        self.assertEqual(updated.cash_balance, Decimal('500.00'))

    def test_update_cash_balance_nonexistent_portfolio(self):
        success = self.service.update_cash_balance(
            uuid4(), 
            Decimal('500.00'), 
            'deposit'
        )
        self.assertFalse(success)

    def test_add_activity_entry_with_stock(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        entry = self.service.add_activity_entry(
            portfolio.id,
            'TRADE',
            Decimal('500.00'),
            datetime.now(),
            'AAPL',
            {'commission': '5.00'}
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.activity_type, 'TRADE')
        self.assertEqual(entry.amount, Decimal('500.00'))
        self.assertIsNotNone(entry.stock_id)
        self.assertEqual(entry.raw_data, {'commission': '5.00'})
        
        # Verify stock was created
        stock = self.equity_repo.find_by_symbol("AAPL", "NASDAQ")
        self.assertIsNotNone(stock)

    def test_add_activity_entry_without_stock(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        entry = self.service.add_activity_entry(
            portfolio.id,
            'DIVIDEND',
            Decimal('100.00'),
            datetime.now()
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.activity_type, 'DIVIDEND')
        self.assertIsNone(entry.stock_id)

    def test_add_activity_entry_nonexistent_portfolio(self):
        entry = self.service.add_activity_entry(
            uuid4(),  # Nonexistent portfolio
            'TRADE',
            Decimal('500.00'),
            datetime.now(),
            'AAPL'
        )
        self.assertIsNone(entry)

    def test_get_holdings(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        # Add multiple holdings
        self.service.add_equity_holding(portfolio.id, "AAPL", Decimal('100'), Decimal('1000.00'))
        self.service.add_equity_holding(portfolio.id, "GOOGL", Decimal('50'), Decimal('500.00'))
        
        holdings = self.service.get_holdings(portfolio.id)
        self.assertEqual(len(holdings), 2)
        
        symbols = []
        for holding in holdings:
            stock = self.equity_repo.get(holding.equity_id)
            symbols.append(stock.symbol)
        
        self.assertIn("AAPL", symbols)
        self.assertIn("GOOGL", symbols)

    def test_get_activity_entries(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        # Add multiple activity entries
        self.service.add_activity_entry(
            portfolio.id, 'TRADE', Decimal('500.00'), datetime.now(), 'AAPL'
        )
        self.service.add_activity_entry(
            portfolio.id, 'DIVIDEND', Decimal('100.00'), datetime.now()
        )
        self.service.add_activity_entry(
            portfolio.id, 'TRADE', Decimal('300.00'), datetime.now(), 'GOOGL'
        )
        
        # Get all entries
        all_entries = self.service.get_activity_entries(portfolio.id)
        self.assertEqual(len(all_entries), 3)
        
        # Filter by activity type
        trade_entries = self.service.get_activity_entries(portfolio.id, activity_type='TRADE')
        dividend_entries = self.service.get_activity_entries(portfolio.id, activity_type='DIVIDEND')
        
        self.assertEqual(len(trade_entries), 2)
        self.assertEqual(len(dividend_entries), 1)

    def test_import_from_ibkr(self):
        portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")
        
        # Mock IBKR data
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
        
        dividends = [
            {
                'description': 'AAPL Dividend',
                'date': '2024-01-15',
                'amount': Decimal('50.00'),
                'currency': 'USD'
            }
        ]
        
        positions = []  # Not used in current implementation
        
        result = self.service.import_from_ibkr(portfolio.id, trades, dividends, positions)
        self.assertTrue(result.success)
        self.assertEqual(result.trades_imported, 2)
        self.assertEqual(result.dividends_imported, 1)
        self.assertEqual(result.activity_entries_created, 3)
        
        # Verify activity entries were created
        entries = self.service.get_activity_entries(portfolio.id)
        self.assertEqual(len(entries), 3)  # 2 trades + 1 dividend
        
        trade_entries = self.service.get_activity_entries(portfolio.id, activity_type='TRADE')
        dividend_entries = self.service.get_activity_entries(portfolio.id, activity_type='DIVIDEND')
        
        self.assertEqual(len(trade_entries), 2)
        self.assertEqual(len(dividend_entries), 1)
        
        # Verify stocks were created
        aapl_stock = self.equity_repo.find_by_symbol('AAPL', 'NASDAQ')
        googl_stock = self.equity_repo.find_by_symbol('GOOGL', 'NASDAQ')
        self.assertIsNotNone(aapl_stock)
        self.assertIsNotNone(googl_stock)

    def test_import_from_ibkr_nonexistent_portfolio(self):
        result = self.service.import_from_ibkr(uuid4(), [], [], [])
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "PortfolioNotFoundError")

if __name__ == '__main__':
    unittest.main()
