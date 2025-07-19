import unittest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from domain.portfolio.models.holding import Equity, EquityHolding, CashHolding
from domain.portfolio.models.activity_report_entry import ActivityReportEntry
from tests.repositories.portfolio import InMemoryPortfolioRepository
from tests.repositories.equity import InMemoryEquityRepository
from tests.repositories.holdings import InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository
from tests.repositories.activity_report import InMemoryActivityReportEntryRepository
from domain.portfolio.portfolio_errors import DuplicateHoldingError

class PortfolioTestRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryPortfolioRepository()
        self.portfolio_id = uuid4()
        self.tenant_id = uuid4()
        self.portfolio = Portfolio(
            id=self.portfolio_id,
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.repo.save(self.portfolio)

    def test_get_existing_portfolio(self):
        portfolio = self.repo.get(self.portfolio_id)
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.id, self.portfolio_id)
        self.assertEqual(str(portfolio.name), "Test Portfolio")
        # Cash balance should be set to 0 by default in in-memory repo
        self.assertEqual(portfolio.cash_balance, Decimal('0'))

    def test_get_nonexistent_portfolio(self):
        portfolio = self.repo.get(uuid4())
        self.assertIsNone(portfolio)

    def test_find_by_tenant_id(self):
        # Add another portfolio for same tenant
        portfolio2 = Portfolio(
            id=uuid4(),
            tenant_id=self.tenant_id,
            name=PortfolioName("Another Portfolio")
        )
        self.repo.save(portfolio2)

        # Add portfolio for different tenant
        portfolio3 = Portfolio(
            id=uuid4(),
            tenant_id=uuid4(),
            name=PortfolioName("Different Tenant Portfolio")
        )
        self.repo.save(portfolio3)

        portfolios = self.repo.find_by_tenant_id(self.tenant_id)
        self.assertEqual(len(portfolios), 2)
        portfolio_names = [str(p.name) for p in portfolios]
        self.assertIn("Test Portfolio", portfolio_names)
        self.assertIn("Another Portfolio", portfolio_names)

    def test_save_and_update_portfolio(self):
        self.portfolio.rename(PortfolioName("Updated Portfolio"))
        self.repo.save(self.portfolio)
        
        retrieved = self.repo.get(self.portfolio_id)
        self.assertEqual(str(retrieved.name), "Updated Portfolio")

    def test_delete_portfolio(self):
        self.repo.delete(self.portfolio_id)
        portfolio = self.repo.get(self.portfolio_id)
        self.assertIsNone(portfolio)

    def test_find_by_name(self):
        # Test finding existing portfolio by name
        portfolio = self.repo.find_by_name(self.tenant_id, "Test Portfolio")
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.id, self.portfolio_id)
        self.assertEqual(str(portfolio.name), "Test Portfolio")

        # Test with nonexistent name
        nonexistent = self.repo.find_by_name(self.tenant_id, "Nonexistent Portfolio")
        self.assertIsNone(nonexistent)

        # Test with different tenant
        different_tenant = self.repo.find_by_name(uuid4(), "Test Portfolio")
        self.assertIsNone(different_tenant)

    def test_exists(self):
        # Test existing portfolio
        self.assertTrue(self.repo.assert_portfolio_exists(self.portfolio_id))
        
        # Test nonexistent portfolio
        self.assertFalse(self.repo.assert_portfolio_exists(uuid4()))
        
        # Test call history
        self.assertTrue(self.repo.assert_method_called('exists', 2))

class InMemoryEquityHoldingRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryEquityHoldingRepository()
        self.portfolio_id = uuid4()
        self.equity_id = uuid4()
        self.holding_id = uuid4()
        self.holding = EquityHolding(
            id=self.holding_id,
            portfolio_id=self.portfolio_id,
            equity_id=self.equity_id,
            quantity=Decimal('100'),
            cost_basis=Decimal('1000.00'),
            current_value=Decimal('1100.00')
        )
        self.repo.save(self.holding)

    def test_get_existing_holding(self):
        holding = self.repo.get(self.holding_id)
        self.assertIsNotNone(holding)
        self.assertEqual(holding.id, self.holding_id)
        self.assertEqual(holding.quantity, Decimal('100'))

    def test_get_nonexistent_holding(self):
        holding = self.repo.get(uuid4())
        self.assertIsNone(holding)

    def test_find_by_portfolio_id(self):
        # Add another holding for same portfolio
        holding2 = EquityHolding(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=uuid4(),
            quantity=Decimal('50'),
            cost_basis=Decimal('500.00'),
            current_value=Decimal('550.00')
        )
        self.repo.save(holding2)

        # Add holding for different portfolio
        holding3 = EquityHolding(
            id=uuid4(),
            portfolio_id=uuid4(),
            equity_id=uuid4(),
            quantity=Decimal('25'),
            cost_basis=Decimal('250.00'),
            current_value=Decimal('275.00')
        )
        self.repo.save(holding3)

        holdings = self.repo.find_by_portfolio_id(self.portfolio_id)
        self.assertEqual(len(holdings), 2)
        quantities = [h.quantity for h in holdings]
        self.assertIn(Decimal('100'), quantities)
        self.assertIn(Decimal('50'), quantities)

    def test_find_by_portfolio_id_with_pagination(self):
        # Add multiple holdings
        for i in range(5):
            holding = EquityHolding(
                id=uuid4(),
                portfolio_id=self.portfolio_id,
                equity_id=uuid4(),
                quantity=Decimal(str(i * 10)),
                cost_basis=Decimal(str(i * 100)),
                current_value=Decimal(str(i * 110))
            )
            self.repo.save(holding)

        # Test pagination
        first_page = self.repo.find_by_portfolio_id(self.portfolio_id, limit=3, offset=0)
        second_page = self.repo.find_by_portfolio_id(self.portfolio_id, limit=3, offset=3)
        
        self.assertEqual(len(first_page), 3)
        self.assertEqual(len(second_page), 3)  # Original holding + 2 more

    def test_find_by_portfolio_and_equity(self):
        holding = self.repo.find_by_portfolio_and_equity(self.portfolio_id, self.equity_id)
        self.assertIsNotNone(holding)
        self.assertEqual(holding.id, self.holding_id)

        # Test with nonexistent combination
        nonexistent = self.repo.find_by_portfolio_and_equity(uuid4(), uuid4())
        self.assertIsNone(nonexistent)

    def test_save_duplicate_holding_raises_error(self):
        duplicate_holding = EquityHolding(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=self.equity_id,  # Same equity
            quantity=Decimal('200'),
            cost_basis=Decimal('2000.00'),
            current_value=Decimal('2200.00')
        )
        
        with self.assertRaises(DuplicateHoldingError):
            self.repo.save(duplicate_holding)

    def test_update_existing_holding(self):
        self.holding.update_quantity(Decimal('150'))
        self.repo.save(self.holding)
        
        retrieved = self.repo.get(self.holding_id)
        self.assertEqual(retrieved.quantity, Decimal('150'))

    def test_delete_holding(self):
        self.repo.delete(self.holding_id)
        holding = self.repo.get(self.holding_id)
        self.assertIsNone(holding)

    def test_batch_save(self):
        holdings = []
        for i in range(3):
            holding = EquityHolding(
                id=uuid4(),
                portfolio_id=self.portfolio_id,
                equity_id=uuid4(),
                quantity=Decimal(str(i * 10)),
                cost_basis=Decimal(str(i * 100)),
                current_value=Decimal(str(i * 110))
            )
            holdings.append(holding)

        self.repo.batch_save(holdings)
        
        all_holdings = self.repo.find_by_portfolio_id(self.portfolio_id)
        self.assertEqual(len(all_holdings), 4)  # Original + 3 new


class InMemoryCashHoldingRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryCashHoldingRepository()
        self.portfolio_id = uuid4()
        self.holding_id = uuid4()
        self.cash_holding = CashHolding(
            id=self.holding_id,
            portfolio_id=self.portfolio_id,
            currency='USD',
            balance=Decimal('1000.00')
        )
        self.repo.save(self.cash_holding)

    def test_get_existing_cash_holding(self):
        holding = self.repo.get(self.holding_id)
        self.assertIsNotNone(holding)
        self.assertEqual(holding.id, self.holding_id)
        self.assertEqual(holding.balance, Decimal('1000.00'))

    def test_get_nonexistent_cash_holding(self):
        holding = self.repo.get(uuid4())
        self.assertIsNone(holding)

    def test_find_by_portfolio_id(self):
        # Add another cash holding for same portfolio
        holding2 = CashHolding(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            currency='EUR',
            balance=Decimal('500.00')
        )
        self.repo.save(holding2)

        # Add cash holding for different portfolio
        holding3 = CashHolding(
            id=uuid4(),
            portfolio_id=uuid4(),
            currency='USD',
            balance=Decimal('250.00')
        )
        self.repo.save(holding3)

        holdings = self.repo.find_by_portfolio_id(self.portfolio_id)
        self.assertEqual(len(holdings), 2)
        currencies = [h.currency for h in holdings]
        self.assertIn('USD', currencies)
        self.assertIn('EUR', currencies)

    def test_find_by_portfolio_and_currency(self):
        holding = self.repo.find_by_portfolio_and_currency(self.portfolio_id, 'USD')
        self.assertIsNotNone(holding)
        self.assertEqual(holding.id, self.holding_id)

        # Test with nonexistent combination
        nonexistent = self.repo.find_by_portfolio_and_currency(uuid4(), 'USD')
        self.assertIsNone(nonexistent)

    def test_delete_cash_holding(self):
        self.repo.delete(self.holding_id)
        holding = self.repo.get(self.holding_id)
        self.assertIsNone(holding)

    def test_exists(self):
        self.assertTrue(self.repo.exists(self.holding_id))
        self.assertFalse(self.repo.exists(uuid4()))

class InMemoryActivityReportEntryRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryActivityReportEntryRepository()
        self.portfolio_id = uuid4()
        self.equity_id = uuid4()
        self.entry_id = uuid4()
        self.entry = ActivityReportEntry(
            id=self.entry_id,
            portfolio_id=self.portfolio_id,
            equity_id=self.equity_id,
            currency='USD',
            activity_type='TRADE',
            amount=Decimal('500.00'),
            date=datetime.now(),
            raw_data={}
        )
        self.repo.save(self.entry)

    def test_get_existing_entry(self):
        entry = self.repo.get(self.entry_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.id, self.entry_id)
        self.assertEqual(entry.activity_type, 'TRADE')

    def test_get_nonexistent_entry(self):
        entry = self.repo.get(uuid4())
        self.assertIsNone(entry)

    def test_find_by_portfolio_id(self):
        # Add another entry for same portfolio
        entry2 = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=None,
            currency='USD',
            activity_type='DIVIDEND',
            amount=Decimal('100.00'),
            date=datetime.now(),
            raw_data={}
        )
        self.repo.save(entry2)

        # Add entry for different portfolio
        entry3 = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=uuid4(),
            equity_id=self.equity_id,
            currency='USD',
            activity_type='TRADE',
            amount=Decimal('200.00'),
            date=datetime.now(),
            raw_data={}
        )
        self.repo.save(entry3)

        entries = self.repo.find_by_portfolio_id(self.portfolio_id)
        self.assertEqual(len(entries), 2)
        activity_types = [e.activity_type for e in entries]
        self.assertIn('TRADE', activity_types)
        self.assertIn('DIVIDEND', activity_types)

    def test_find_by_portfolio_id_with_activity_type_filter(self):
        # Add entries with different activity types
        dividend_entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=None,
            currency='USD',
            activity_type='DIVIDEND',
            amount=Decimal('100.00'),
            date=datetime.now(),
            raw_data={}
        )
        self.repo.save(dividend_entry)

        fee_entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=None,
            currency='USD',
            activity_type='FEE',
            amount=Decimal('-5.00'),
            date=datetime.now(),
            raw_data={}
        )
        self.repo.save(fee_entry)

        # Filter by activity type
        trade_entries = self.repo.find_by_portfolio_id(self.portfolio_id, activity_type='TRADE')
        dividend_entries = self.repo.find_by_portfolio_id(self.portfolio_id, activity_type='DIVIDEND')
        
        self.assertEqual(len(trade_entries), 1)
        self.assertEqual(len(dividend_entries), 1)
        self.assertEqual(trade_entries[0].activity_type, 'TRADE')
        self.assertEqual(dividend_entries[0].activity_type, 'DIVIDEND')

    def test_delete_entry(self):
        self.repo.delete(self.entry_id)
        entry = self.repo.get(self.entry_id)
        self.assertIsNone(entry)

    def test_batch_save(self):
        entries = []
        for i in range(3):
            entry = ActivityReportEntry(
                id=uuid4(),
                portfolio_id=self.portfolio_id,
                equity_id=self.equity_id,
                currency='USD',
                activity_type='TRADE',
                amount=Decimal(str(i * 100)),
                date=datetime.now(),
                raw_data={}
            )
            entries.append(entry)

        self.repo.batch_save(entries)
        
        all_entries = self.repo.find_by_portfolio_id(self.portfolio_id)
        self.assertEqual(len(all_entries), 4)  # Original + 3 new

class InMemoryEquityRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryEquityRepository()
        self.equity_id = uuid4()
        self.equity = Equity(
            id=self.equity_id,
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ'
        )
        self.repo.save(self.equity)

    def test_get_existing_equity(self):
        equity = self.repo.get(self.equity_id)
        self.assertIsNotNone(equity)
        self.assertEqual(equity.symbol, 'AAPL')
        self.assertEqual(equity.name, 'Apple Inc.')

    def test_get_nonexistent_equity(self):
        equity = self.repo.get(uuid4())
        self.assertIsNone(equity)

    def test_find_by_symbol(self):
        equity = self.repo.find_by_symbol('AAPL', 'NASDAQ')
        self.assertIsNotNone(equity)
        self.assertEqual(equity.id, self.equity_id)

        # Test with nonexistent symbol
        nonexistent = self.repo.find_by_symbol('NONEXISTENT', 'NASDAQ')
        self.assertIsNone(nonexistent)

    def test_update_equity(self):
        # Update equity using the update_info method
        self.equity.update_info(name='Apple Inc. (Updated)')
        self.repo.save(self.equity)
        
        retrieved = self.repo.get(self.equity_id)
        self.assertEqual(retrieved.name, 'Apple Inc. (Updated)')

    def test_delete_equity(self):
        self.repo.delete(self.equity_id)
        equity = self.repo.get(self.equity_id)
        self.assertIsNone(equity)

    def test_exists(self):
        self.assertTrue(self.repo.exists(self.equity_id))
        self.assertFalse(self.repo.exists(uuid4()))

    def test_search(self):
        # Add more equities for search testing
        equity2 = Equity(
            id=uuid4(),
            symbol='MSFT',
            name='Microsoft Corporation',
            exchange='NASDAQ'
        )
        self.repo.save(equity2)

        # Search by symbol
        results = self.repo.search('AAPL')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].symbol, 'AAPL')

        # Search by name
        results = self.repo.search('Microsoft')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].symbol, 'MSFT')

        # Search with limit
        results = self.repo.search('', limit=1)
        self.assertEqual(len(results), 1)

if __name__ == '__main__':
    unittest.main()
