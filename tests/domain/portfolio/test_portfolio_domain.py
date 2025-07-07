import unittest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from domain.portfolio.models.holding import EquityHolding
from domain.portfolio.models.activity_report_entry import ActivityReportEntry
from domain.portfolio.models.enums import Currency
from domain.portfolio.stock import Stock
from domain.portfolio.portfolio_events import (
    PortfolioCreated, PortfolioRenamed, PortfolioDeleted, HoldingAdded, 
    HoldingRemoved, HoldingUpdated, ActivityReportEntryAdded, PortfolioRecalculated
)
from domain.portfolio.portfolio_errors import (
    InvalidPortfolioNameError, OwnershipMismatchError,
    StockNotFoundError
)
from unittest.mock import Mock

class PortfolioNameTestCase(unittest.TestCase):
    def test_valid_name(self):
        name = PortfolioName("My Portfolio")
        self.assertEqual(str(name), "My Portfolio")

    def test_empty_name_raises_error(self):
        with self.assertRaises(InvalidPortfolioNameError):
            PortfolioName("")

    def test_whitespace_only_name_raises_error(self):
        with self.assertRaises(InvalidPortfolioNameError):
            PortfolioName("   ")

    def test_too_long_name_raises_error(self):
        long_name = "a" * 101
        with self.assertRaises(InvalidPortfolioNameError):
            PortfolioName(long_name)

    def test_name_equality(self):
        name1 = PortfolioName("Test")
        name2 = PortfolioName("Test")
        name3 = PortfolioName("Different")
        
        self.assertEqual(name1, name2)
        self.assertNotEqual(name1, name3)

    def test_name_normalization(self):
        name = PortfolioName("  Test Portfolio  ")
        self.assertEqual(str(name), "Test Portfolio")

class EquityHoldingTestCase(unittest.TestCase):
    def setUp(self):
        self.holding_id = uuid4()
        self.portfolio_id = uuid4()
        self.equity_id = uuid4()
        self.holding = EquityHolding(
            id=self.holding_id,
            portfolio_id=self.portfolio_id,
            equity_id=self.equity_id,
            quantity=Decimal('100'),
            cost_basis=Decimal('1000.00')
        )

    def test_holding_creation(self):
        self.assertEqual(self.holding.id, self.holding_id)
        self.assertEqual(self.holding.portfolio_id, self.portfolio_id)
        self.assertEqual(self.holding.equity_id, self.equity_id)
        self.assertEqual(self.holding.quantity, Decimal('100'))
        self.assertEqual(self.holding.cost_basis, Decimal('1000.00'))
        self.assertEqual(self.holding.current_value, Decimal('0'))

    def test_update_quantity_records_event(self):
        self.holding.update_quantity(Decimal('150'))
        events = self.holding.pull_events()
        
        self.assertEqual(self.holding.quantity, Decimal('150'))
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], HoldingUpdated)

    def test_update_cost_basis_records_event(self):
        self.holding.update_cost_basis(Decimal('1200.00'))
        events = self.holding.pull_events()
        
        self.assertEqual(self.holding.cost_basis, Decimal('1200.00'))
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], HoldingUpdated)

    def test_update_current_value(self):
        self.holding.update_current_value(Decimal('1500.00'))
        self.assertEqual(self.holding.current_value, Decimal('1500.00'))

class ActivityReportEntryTestCase(unittest.TestCase):
    def setUp(self):
        self.entry_id = uuid4()
        self.portfolio_id = uuid4()
        self.equity_id = uuid4()
        self.entry = ActivityReportEntry(
            id=self.entry_id,
            portfolio_id=self.portfolio_id,
            equity_id=self.equity_id,
            activity_type='TRADE',
            amount=Decimal('500.00'),
            currency=Currency.USD,
            date=datetime.now()
        )

    def test_entry_creation(self):
        self.assertEqual(self.entry.id, self.entry_id)
        self.assertEqual(self.entry.portfolio_id, self.portfolio_id)
        self.assertEqual(self.entry.equity_id, self.equity_id)
        self.assertEqual(self.entry.activity_type, 'TRADE')
        self.assertEqual(self.entry.amount, Decimal('500.00'))
        self.assertEqual(self.entry.raw_data, {})

    def test_entry_with_raw_data(self):
        raw_data = {'source': 'IBKR', 'commission': '5.00'}
        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=None,
            activity_type='DIVIDEND',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            date=datetime.now(),
            raw_data=raw_data
        )
        self.assertEqual(entry.raw_data, raw_data)
        self.assertIsNone(entry.equity_id)

class PortfolioTestCase(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid4()
        self.tenant_id = uuid4()
        self.portfolio = Portfolio(
            id=self.portfolio_id,
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )

    def test_portfolio_creation_records_event(self):
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PortfolioCreated)
        self.assertEqual(events[0].portfolio_id, self.portfolio_id)
        self.assertEqual(events[0].tenant_id, self.tenant_id)

    def test_portfolio_rename_records_event(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        new_name = PortfolioName("Renamed Portfolio")
        self.portfolio.rename(new_name)
        events = self.portfolio.pull_events()
        
        self.assertEqual(self.portfolio.name, new_name)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PortfolioRenamed)
        self.assertEqual(events[0].old_name, "Test Portfolio")
        self.assertEqual(events[0].new_name, "Renamed Portfolio")

    def test_portfolio_rename_same_name_no_event(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        self.portfolio.rename(PortfolioName("Test Portfolio"))
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 0)

    def test_portfolio_delete_records_event(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        self.portfolio.delete()
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PortfolioDeleted)

    def test_recalculate_records_event(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        self.portfolio.recalculate('batch_update')
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PortfolioRecalculated)
        self.assertEqual(events[0].recalculation_type, 'batch_update')

    def test_add_equity_holding_with_valid_stock(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        # Mock equity repository
        equity_repo = Mock()
        equity = Stock(id=uuid4(), symbol='AAPL')
        equity_repo.get.return_value = equity
        
        holding = EquityHolding(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=equity.id,
            quantity=Decimal('100'),
            cost_basis=Decimal('1000.00')
        )
        
        self.portfolio.add_equity_holding(holding, equity_repo)
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], HoldingAdded)
        equity_repo.get.assert_called_once_with(equity.id)

    def test_add_equity_holding_with_invalid_stock_raises_error(self):
        # Mock equity repository
        equity_repo = Mock()
        equity_repo.get.return_value = None
        
        holding = EquityHolding(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=uuid4(),
            quantity=Decimal('100'),
            cost_basis=Decimal('1000.00')
        )
        
        with self.assertRaises(StockNotFoundError):
            self.portfolio.add_equity_holding(holding, equity_repo)

    def test_add_equity_holding_ownership_mismatch_raises_error(self):
        # Mock equity repository
        equity_repo = Mock()
        
        holding = EquityHolding(
            id=uuid4(),
            portfolio_id=uuid4(),  # Different portfolio ID
            equity_id=uuid4(),
            quantity=Decimal('100'),
            cost_basis=Decimal('1000.00')
        )
        
        with self.assertRaises(OwnershipMismatchError):
            self.portfolio.add_equity_holding(holding, equity_repo)

    def test_remove_equity_holding_records_event(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        holding_id = uuid4()
        equity_id = uuid4()
        
        self.portfolio.remove_equity_holding(holding_id, equity_id)
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], HoldingRemoved)
        self.assertEqual(events[0].holding_id, holding_id)
        self.assertEqual(events[0].stock_id, equity_id)  # Event still uses stock_id for compatibility

    def test_add_activity_entry_with_valid_stock(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        # Mock equity repository
        equity_repo = Mock()
        equity = Stock(id=uuid4(), symbol='AAPL')
        equity_repo.get.return_value = equity
        
        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=equity.id,
            activity_type='TRADE',
            amount=Decimal('500.00'),
            currency=Currency.USD,
            date=datetime.now()
        )
        
        self.portfolio.add_activity_entry(entry, equity_repo)
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ActivityReportEntryAdded)
        equity_repo.get.assert_called_once_with(equity.id)

    def test_add_activity_entry_without_stock(self):
        # Clear creation event
        self.portfolio.pull_events()
        
        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=self.portfolio_id,
            equity_id=None,
            activity_type='DIVIDEND',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            date=datetime.now()
        )
        
        self.portfolio.add_activity_entry(entry)
        events = self.portfolio.pull_events()
        
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], ActivityReportEntryAdded)

    def test_add_activity_entry_ownership_mismatch_raises_error(self):
        entry = ActivityReportEntry(
            id=uuid4(),
            portfolio_id=uuid4(),  # Different portfolio ID
            equity_id=None,
            activity_type='DIVIDEND',
            amount=Decimal('100.00'),
            currency=Currency.USD,
            date=datetime.now()
        )
        
        with self.assertRaises(OwnershipMismatchError):
            self.portfolio.add_activity_entry(entry)

if __name__ == '__main__':
    unittest.main()
