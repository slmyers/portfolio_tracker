"""
Unit tests for dividend currency parsing in IBKR CSV import.

This test validates that dividend activity report entries correctly preserve
the currency information from the parsed IBKR CSV data.
"""
import unittest
import tempfile
import os
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from core.csv.ibkr import IbkrCsvParser
from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.models.enums import Currency
from tests.repositories.portfolio import InMemoryPortfolioRepository
from tests.repositories.equity import InMemoryEquityRepository
from tests.repositories.holdings import InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository
from tests.repositories.activity_report import InMemoryActivityReportEntryRepository


class MockLogger:
    def debug(self, msg, *args, **kwargs):
        pass
    def info(self, msg, *args, **kwargs):
        pass
    def warning(self, msg, *args, **kwargs):
        pass


class DividendCurrencyParsingTest(unittest.TestCase):
    """Test that dividend parsing correctly preserves currency information."""

    def setUp(self):
        """Set up test dependencies."""
        self.portfolio_repo = InMemoryPortfolioRepository()
        self.equity_repo = InMemoryEquityRepository()
        self.equity_holding_repo = InMemoryEquityHoldingRepository()
        self.cash_holding_repo = InMemoryCashHoldingRepository()
        self.activity_entry_repo = InMemoryActivityReportEntryRepository()
        
        self.service = PortfolioService(
            self.portfolio_repo,
            self.equity_repo,
            self.equity_holding_repo,
            self.cash_holding_repo,
            self.activity_entry_repo
        )
        
        self.tenant_id = uuid4()
        self.portfolio = self.service.create_portfolio(self.tenant_id, "Test Portfolio")

    def create_test_ibkr_csv_with_cad_dividends(self):
        """Create a test CSV file with CAD dividend entries."""
        csv_content = '''Statement,Header,Field Name,Field Value
Statement,Data,Account,U1234567
Statement,Data,Period,"January 1, 2025 - December 31, 2025"
Statement,Data,WhenGenerated,"2025-07-12, 10:30:00 EST"
Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,CAD,2025-01-03,XAW(CA46435D1096) Cash Dividend CAD 0.39601 per Share (Ordinary Dividend),25.34
Dividends,Data,CAD,2025-03-07,REI.UN(CA7669101031) Cash Dividend CAD 0.0965 per Share (Ordinary Dividend),11.48
Dividends,Data,USD,2025-03-28,QQQM(US46138G6492) Cash Dividend USD 0.31763 per Share (Ordinary Dividend),4.13
Dividends,Data,Total,,,40.95
'''
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        return temp_file.name

    def test_dividend_parsing_preserves_currency(self):
        """Test that CSV parsing correctly extracts currency from dividend entries."""
        csv_file = self.create_test_ibkr_csv_with_cad_dividends()
        
        try:
            parser = IbkrCsvParser(logger=MockLogger())
            parser.parse(csv_file)

            # Verify parsed dividends contain correct currency
            dividends = parser.dividends
            self.assertEqual(len(dividends), 3)  # Excluding total row
            
            # Check CAD dividends
            cad_dividends = [d for d in dividends if d['currency'] == 'CAD']
            self.assertEqual(len(cad_dividends), 2)
            
            xaw_dividend = next(d for d in cad_dividends if 'XAW' in d['description'])
            self.assertEqual(xaw_dividend['currency'], 'CAD')
            self.assertEqual(xaw_dividend['amount'], 25.34)
            
            rei_dividend = next(d for d in cad_dividends if 'REI.UN' in d['description'])
            self.assertEqual(rei_dividend['currency'], 'CAD')
            self.assertEqual(rei_dividend['amount'], 11.48)
            
            # Check USD dividend
            usd_dividends = [d for d in dividends if d['currency'] == 'USD']
            self.assertEqual(len(usd_dividends), 1)
            
            qqqm_dividend = usd_dividends[0]
            self.assertEqual(qqqm_dividend['currency'], 'USD')
            self.assertEqual(qqqm_dividend['amount'], 4.13)
            
        finally:
            os.unlink(csv_file)

    def test_dividend_import_preserves_currency_in_activity_entries(self):
        """Test that importing dividends preserves currency in activity report entries."""
        csv_file = self.create_test_ibkr_csv_with_cad_dividends()
        
        try:
            parser = IbkrCsvParser(logger=MockLogger())
            parser.parse(csv_file)
            
            # Import dividends into portfolio
            result = self.service.import_from_ibkr(
                self.portfolio.id,
                trades=[],  # No trades
                dividends=parser.dividends,
                positions=[]  # No positions
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.dividends_imported, 3)
            
            # Get activity entries and verify currencies
            activities = self.service.get_activity_entries(self.portfolio.id, activity_type='DIVIDEND')
            self.assertEqual(len(activities), 3)
            
            # Check CAD dividend entries
            cad_activities = [a for a in activities if a.currency == Currency.CAD]
            self.assertEqual(len(cad_activities), 2)
            
            # Verify specific CAD entries
            xaw_activity = next((a for a in cad_activities if 'XAW' in a.raw_data.get('description', '')), None)
            self.assertIsNotNone(xaw_activity)
            self.assertEqual(xaw_activity.currency, Currency.CAD)
            # Convert float to Decimal for comparison
            self.assertEqual(Decimal(str(xaw_activity.amount)), Decimal('25.34'))
            self.assertEqual(xaw_activity.raw_data['currency'], 'CAD')
            
            rei_activity = next((a for a in cad_activities if 'REI.UN' in a.raw_data.get('description', '')), None)
            self.assertIsNotNone(rei_activity)
            self.assertEqual(rei_activity.currency, Currency.CAD)
            # Convert float to Decimal for comparison
            self.assertEqual(Decimal(str(rei_activity.amount)), Decimal('11.48'))
            self.assertEqual(rei_activity.raw_data['currency'], 'CAD')
            
            # Check USD dividend entry
            usd_activities = [a for a in activities if a.currency == Currency.USD]
            self.assertEqual(len(usd_activities), 1)
            
            qqqm_activity = usd_activities[0]
            self.assertEqual(qqqm_activity.currency, Currency.USD)
            # Convert float to Decimal for comparison
            self.assertEqual(Decimal(str(qqqm_activity.amount)), Decimal('4.13'))
            self.assertEqual(qqqm_activity.raw_data['currency'], 'USD')
            
        finally:
            os.unlink(csv_file)

    def test_add_activity_entry_with_cad_currency_from_raw_data(self):
        """Test direct addition of activity entry with CAD currency in raw_data."""
        raw_data = {
            'currency': 'CAD',
            'date': '2025-07-12',
            'description': 'Test CAD Dividend',
            'amount': 50.00
        }
        
        entry = self.service.add_activity_entry(
            portfolio_id=self.portfolio.id,
            activity_type='DIVIDEND',
            amount=Decimal('50.00'),
            date=datetime.now(),
            raw_data=raw_data
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.currency, Currency.CAD)
        self.assertEqual(entry.raw_data['currency'], 'CAD')

    def test_add_activity_entry_defaults_to_usd_when_no_currency(self):
        """Test that activity entry defaults to USD when no currency is specified."""
        entry = self.service.add_activity_entry(
            portfolio_id=self.portfolio.id,
            activity_type='DIVIDEND',
            amount=Decimal('50.00'),
            date=datetime.now()
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.currency, Currency.USD)

    def test_add_activity_entry_handles_invalid_currency(self):
        """Test that activity entry defaults to USD when invalid currency is provided."""
        raw_data = {
            'currency': 'INVALID',
            'description': 'Test Invalid Currency'
        }
        
        entry = self.service.add_activity_entry(
            portfolio_id=self.portfolio.id,
            activity_type='DIVIDEND',
            amount=Decimal('50.00'),
            date=datetime.now(),
            raw_data=raw_data
        )
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.currency, Currency.USD)  # Should default to USD


if __name__ == '__main__':
    unittest.main()
