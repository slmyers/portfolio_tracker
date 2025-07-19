import unittest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from domain.portfolio.models.holding import EquityHolding, CashHolding
from domain.portfolio.models.activity_report_entry import ActivityReportEntry
from domain.portfolio.models.enums import Currency
from domain.portfolio.stock import Stock
from domain.portfolio.repository.postgres_portfolio import PostgresPortfolioRepository
from domain.portfolio.repository.postgres_holdings import PostgresHoldingRepository
from domain.portfolio.repository.postgres_activity_report_entry import PostgresActivityReportEntryRepository
from domain.portfolio.repository.postgres_equity import PostgresEquityRepository
from domain.portfolio.repository.postgres_cash_holdings import PostgresCashHoldingRepository
from core.persistence.postgres import PostgresPool
from core.config.config import get_test_postgres_config

class PostgresPortfolioRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = get_test_postgres_config()
        cls.db = PostgresPool(cls.config)
        cls.repo = PostgresPortfolioRepository(cls.db)
        cls.cash_repo = PostgresCashHoldingRepository(cls.db)

    def setUp(self):
        self.conn_ctx = self.db.connection()
        self.conn, _ = self.conn_ctx.__enter__()
        self.conn.autocommit = False
        
        self.portfolio_id = uuid4()
        self.tenant_id = uuid4()
        self.portfolio = Portfolio(
            id=self.portfolio_id,
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.repo.save(self.portfolio, conn=self.conn)
        
        # Create initial cash holding
        self.cash_holding = CashHolding(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            currency=Currency.USD,
            balance=Decimal('1000.00')
        )
        self.cash_repo.save(self.cash_holding, conn=self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn_ctx.__exit__(None, None, None)

    def test_get_existing_portfolio(self):
        portfolio = self.repo.get(self.portfolio_id, conn=self.conn)
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.id, self.portfolio_id)
        self.assertEqual(str(portfolio.name), "Test Portfolio")
        self.assertEqual(portfolio.cash_balance, Decimal('1000.00'))

    def test_get_nonexistent_portfolio(self):
        portfolio = self.repo.get(uuid4(), conn=self.conn)
        self.assertIsNone(portfolio)

    def test_find_by_tenant_id(self):
        # Add another portfolio for same tenant
        portfolio2 = Portfolio(
            id=uuid4(),
            tenant_id=self.tenant_id,
            name=PortfolioName("Another Portfolio")
        )
        self.repo.save(portfolio2, conn=self.conn)

        portfolios = self.repo.find_by_tenant_id(self.tenant_id, conn=self.conn)
        self.assertEqual(len(portfolios), 2)
        portfolio_names = [str(p.name) for p in portfolios]
        self.assertIn("Test Portfolio", portfolio_names)
        self.assertIn("Another Portfolio", portfolio_names)

    def test_save_and_update_portfolio(self):
        self.portfolio.rename(PortfolioName("Updated Portfolio"))
        self.repo.save(self.portfolio, conn=self.conn)
        
        retrieved = self.repo.get(self.portfolio_id, conn=self.conn)
        self.assertEqual(str(retrieved.name), "Updated Portfolio")

    def test_delete_portfolio(self):
        self.repo.delete(self.portfolio_id, conn=self.conn)
        portfolio = self.repo.get(self.portfolio_id, conn=self.conn)
        self.assertIsNone(portfolio)

class PostgresStockRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = get_test_postgres_config()
        cls.db = PostgresPool(cls.config)
        cls.repo = PostgresEquityRepository(cls.db)

    def setUp(self):
        self.conn_ctx = self.db.connection()
        self.conn, _ = self.conn_ctx.__enter__()
        self.conn.autocommit = False
        
        self.stock_id = uuid4()
        self.stock = Stock(
            id=self.stock_id,
            symbol='AAPL',
            name='Apple Inc.',
            exchange='NASDAQ'
        )
        self.repo.save(self.stock, conn=self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn_ctx.__exit__(None, None, None)

    def test_get_existing_stock(self):
        stock = self.repo.get(self.stock_id, conn=self.conn)
        self.assertIsNotNone(stock)
        self.assertEqual(stock.symbol, 'AAPL')
        self.assertEqual(stock.name, 'Apple Inc.')

    def test_find_by_symbol(self):
        stock = self.repo.find_by_symbol('AAPL', 'NASDAQ', conn=self.conn)
        self.assertIsNotNone(stock)
        self.assertEqual(stock.id, self.stock_id)

    def test_save_and_update_stock(self):
        self.stock.update_info(name='Apple Inc. (Updated)')
        self.repo.save(self.stock, conn=self.conn)
        
        retrieved = self.repo.get(self.stock_id, conn=self.conn)
        self.assertEqual(retrieved.name, 'Apple Inc. (Updated)')

class PostgresHoldingRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = get_test_postgres_config()
        cls.db = PostgresPool(cls.config)
        cls.portfolio_repo = PostgresPortfolioRepository(cls.db)
        cls.stock_repo = PostgresEquityRepository(cls.db)
        cls.repo = PostgresHoldingRepository(cls.db)

    def setUp(self):
        self.conn_ctx = self.db.connection()
        self.conn, _ = self.conn_ctx.__enter__()
        self.conn.autocommit = False
        
        # Create portfolio
        self.portfolio_id = uuid4()
        self.tenant_id = uuid4()
        portfolio = Portfolio(
            id=self.portfolio_id,
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.portfolio_repo.save(portfolio, conn=self.conn)
        
        # Create stock
        self.stock_id = uuid4()
        stock = Stock(
            id=self.stock_id,
            symbol='AAPL',
            name='Apple Inc.'
        )
        self.stock_repo.save(stock, conn=self.conn)
        
        # Create holding
        self.holding_id = uuid4()
        self.holding = EquityHolding(
            id=self.holding_id,
            portfolio_id=self.portfolio_id,
            equity_id=self.stock_id,
            quantity=Decimal('100'),
            cost_basis=Decimal('1000.00')
        )
        self.repo.save(self.holding, conn=self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn_ctx.__exit__(None, None, None)

    def test_get_existing_holding(self):
        holding = self.repo.get(self.holding_id, conn=self.conn)
        self.assertIsNotNone(holding)
        self.assertEqual(holding.quantity, Decimal('100'))

    def test_find_by_portfolio_id(self):
        holdings = self.repo.find_by_portfolio_id(self.portfolio_id, conn=self.conn)
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].id, self.holding_id)

    def test_find_by_portfolio_and_stock(self):
        holding = self.repo.find_by_portfolio_and_stock(
            self.portfolio_id, 
            self.stock_id, 
            conn=self.conn
        )
        self.assertIsNotNone(holding)
        self.assertEqual(holding.id, self.holding_id)

    def test_update_holding(self):
        self.holding.update_quantity(Decimal('150'))
        self.repo.save(self.holding, conn=self.conn)
        
        retrieved = self.repo.get(self.holding_id, conn=self.conn)
        self.assertEqual(retrieved.quantity, Decimal('150'))

class PostgresActivityReportEntryRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = get_test_postgres_config()
        cls.db = PostgresPool(cls.config)
        cls.portfolio_repo = PostgresPortfolioRepository(cls.db)
        cls.stock_repo = PostgresEquityRepository(cls.db)
        cls.repo = PostgresActivityReportEntryRepository(cls.db)

    def setUp(self):
        self.conn_ctx = self.db.connection()
        self.conn, _ = self.conn_ctx.__enter__()
        self.conn.autocommit = False
        
        # Create portfolio
        self.portfolio_id = uuid4()
        self.tenant_id = uuid4()
        portfolio = Portfolio(
            id=self.portfolio_id,
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.portfolio_repo.save(portfolio, conn=self.conn)
        
        # Create stock
        self.stock_id = uuid4()
        stock = Stock(
            id=self.stock_id,
            symbol='AAPL',
            name='Apple Inc.'
        )
        self.stock_repo.save(stock, conn=self.conn)
        
        # Create activity entry
        self.entry_id = uuid4()
        self.entry = ActivityReportEntry(
            id=self.entry_id,
            portfolio_id=self.portfolio_id,
            equity_id=self.stock_id,
            activity_type='TRADE',
            amount=Decimal('500.00'),
            currency=Currency.USD,
            date=datetime.now(),
            raw_data={'commission': '5.00'}
        )
        self.repo.save(self.entry, conn=self.conn)

    def tearDown(self):
        self.conn.rollback()
        self.conn_ctx.__exit__(None, None, None)

    def test_get_existing_entry(self):
        entry = self.repo.get(self.entry_id, conn=self.conn)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.activity_type, 'TRADE')
        self.assertEqual(entry.raw_data, {'commission': '5.00'})

    def test_find_by_portfolio_id(self):
        entries = self.repo.find_by_portfolio_id(self.portfolio_id, conn=self.conn)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, self.entry_id)

    def test_find_by_portfolio_id_with_activity_type_filter(self):
        # Add another entry with different activity type
        dividend_entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=None,
            activity_type='DIVIDEND',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            date=datetime.now()
        )
        self.repo.save(dividend_entry, conn=self.conn)

        trade_entries = self.repo.find_by_portfolio_id(
            self.portfolio_id, 
            activity_type='TRADE', 
            conn=self.conn
        )
        dividend_entries = self.repo.find_by_portfolio_id(
            self.portfolio_id, 
            activity_type='DIVIDEND', 
            conn=self.conn
        )
        
        self.assertEqual(len(trade_entries), 1)
        self.assertEqual(len(dividend_entries), 1)

if __name__ == '__main__':
    unittest.main()
