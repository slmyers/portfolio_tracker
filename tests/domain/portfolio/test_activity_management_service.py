#!/usr/bin/env python3

import unittest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from domain.portfolio.activity_management_service import ActivityManagementService
from domain.portfolio.models.portfolio import Portfolio, PortfolioName
from domain.portfolio.models.enums import Currency
from tests.repositories.portfolio import TestPortfolioRepository
from tests.repositories.equity import TestEquityRepository
from tests.repositories.activity_report import TestActivityReportEntryRepository
from tests.repositories.holdings import TestCashHoldingRepository


class ActivityManagementServiceTest(unittest.TestCase):
    """Test the specialized ActivityManagementService."""

    def setUp(self):
        """Set up test dependencies."""
        self.cash_holding_repo = TestCashHoldingRepository()
        self.portfolio_repo = TestPortfolioRepository(self.cash_holding_repo)
        self.equity_repo = TestEquityRepository()
        self.activity_entry_repo = TestActivityReportEntryRepository()
        
        self.service = ActivityManagementService(
            portfolio_repo=self.portfolio_repo,
            equity_repo=self.equity_repo,
            activity_entry_repo=self.activity_entry_repo
        )
        
        self.tenant_id = uuid4()
        
        # Create a test portfolio
        self.portfolio = Portfolio(
            id=uuid4(),
            tenant_id=self.tenant_id,
            name=PortfolioName("Test Portfolio")
        )
        self.portfolio_repo.save(self.portfolio)

    def test_add_activity_entry_with_stock(self):
        """Test adding an activity entry with stock symbol."""
        entry = self.service.add_activity_entry(
            self.portfolio.id,
            'TRADE',
            Decimal('500.00'),
            datetime.now(),
            'AAPL',
            {'commission': '5.00'}
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.activity_type, 'TRADE')
        self.assertEqual(entry.amount, Decimal('500.00'))
        self.assertEqual(entry.currency, Currency.USD)
        
        # Verify stock was created
        stock = self.equity_repo.find_by_symbol("AAPL", "NASDAQ")
        self.assertIsNotNone(stock)
        self.assertEqual(entry.equity_id, stock.id)
        
        # Verify entry was saved
        saved_entry = self.activity_entry_repo.get(entry.id)
        self.assertIsNotNone(saved_entry)

    def test_add_activity_entry_without_stock(self):
        """Test adding an activity entry without stock symbol."""
        entry = self.service.add_activity_entry(
            self.portfolio.id,
            'DIVIDEND',
            Decimal('100.00'),
            datetime.now()
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.activity_type, 'DIVIDEND')
        self.assertEqual(entry.amount, Decimal('100.00'))
        self.assertEqual(entry.currency, Currency.USD)
        self.assertIsNone(entry.equity_id)
        
        # Verify entry was saved
        saved_entry = self.activity_entry_repo.get(entry.id)
        self.assertIsNotNone(saved_entry)

    def test_add_activity_entry_with_currency_from_raw_data(self):
        """Test that currency is extracted from raw_data."""
        entry = self.service.add_activity_entry(
            self.portfolio.id,
            'DIVIDEND',
            Decimal('100.00'),
            datetime.now(),
            raw_data={'currency': 'CAD', 'description': 'Test dividend'}
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.currency, Currency.CAD)

    def test_add_activity_entry_with_invalid_currency(self):
        """Test that invalid currency defaults to USD."""
        entry = self.service.add_activity_entry(
            self.portfolio.id,
            'DIVIDEND',
            Decimal('100.00'),
            datetime.now(),
            raw_data={'currency': 'INVALID', 'description': 'Test dividend'}
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.currency, Currency.USD)

    def test_add_activity_entry_explicit_currency(self):
        """Test adding activity entry with explicit currency parameter."""
        entry = self.service.add_activity_entry(
            self.portfolio.id,
            'DIVIDEND',
            Decimal('100.00'),
            datetime.now(),
            currency=Currency.CAD
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.currency, Currency.CAD)

    def test_add_activity_entry_nonexistent_portfolio(self):
        """Test adding activity entry to nonexistent portfolio returns None."""
        entry = self.service.add_activity_entry(
            uuid4(),
            'TRADE',
            Decimal('500.00'),
            datetime.now(),
            'AAPL'
        )
        
        self.assertIsNone(entry)

    def test_get_activity_entries(self):
        """Test getting activity entries for a portfolio."""
        # Add multiple activity entries
        self.service.add_activity_entry(
            self.portfolio.id, 'TRADE', Decimal('500.00'), datetime.now(), 'AAPL'
        )
        self.service.add_activity_entry(
            self.portfolio.id, 'DIVIDEND', Decimal('100.00'), datetime.now()
        )
        
        entries = self.service.get_activity_entries(self.portfolio.id)
        self.assertEqual(len(entries), 2)
        
        activity_types = {e.activity_type for e in entries}
        self.assertIn('TRADE', activity_types)
        self.assertIn('DIVIDEND', activity_types)

    def test_get_activity_entries_with_filter(self):
        """Test getting activity entries with activity type filter."""
        # Add multiple activity entries
        self.service.add_activity_entry(
            self.portfolio.id, 'TRADE', Decimal('500.00'), datetime.now(), 'AAPL'
        )
        self.service.add_activity_entry(
            self.portfolio.id, 'TRADE', Decimal('600.00'), datetime.now(), 'GOOGL'
        )
        self.service.add_activity_entry(
            self.portfolio.id, 'DIVIDEND', Decimal('100.00'), datetime.now()
        )
        
        # Get only trade entries
        trade_entries = self.service.get_activity_entries(self.portfolio.id, activity_type='TRADE')
        self.assertEqual(len(trade_entries), 2)
        
        for entry in trade_entries:
            self.assertEqual(entry.activity_type, 'TRADE')
        
        # Get only dividend entries
        dividend_entries = self.service.get_activity_entries(self.portfolio.id, activity_type='DIVIDEND')
        self.assertEqual(len(dividend_entries), 1)
        self.assertEqual(dividend_entries[0].activity_type, 'DIVIDEND')

    def test_get_activity_entries_with_pagination(self):
        """Test getting activity entries with pagination."""
        # Add multiple activity entries
        for i in range(5):
            self.service.add_activity_entry(
                self.portfolio.id, 'TRADE', Decimal(f'{100 + i}.00'), datetime.now(), 'AAPL'
            )
        
        # Get first 3 entries
        entries_page1 = self.service.get_activity_entries(self.portfolio.id, limit=3, offset=0)
        self.assertEqual(len(entries_page1), 3)
        
        # Get next 2 entries
        entries_page2 = self.service.get_activity_entries(self.portfolio.id, limit=3, offset=3)
        self.assertEqual(len(entries_page2), 2)
        
        # Ensure no overlap
        page1_ids = {e.id for e in entries_page1}
        page2_ids = {e.id for e in entries_page2}
        self.assertEqual(len(page1_ids & page2_ids), 0)


if __name__ == '__main__':
    unittest.main()
