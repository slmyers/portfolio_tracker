import unittest
from uuid import uuid4
from decimal import Decimal
from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.repository.in_memory import (
    InMemoryPortfolioRepository, InMemoryEquityRepository,
    InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository,
    InMemoryActivityReportEntryRepository
)
from core.csv.ibkr import IbkrCsvParser
import tempfile
import os

# Mock logger for IBKR parser
class MockLogger:
    def debug(self, msg, *args, **kwargs):
        pass
    def info(self, msg, *args, **kwargs):
        pass
    def warning(self, msg, *args, **kwargs):
        pass

class PortfolioIbkrIntegrationTest(unittest.TestCase):
    def setUp(self):
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
        self.portfolio = self.service.create_portfolio(self.tenant_id, "IBKR Import Test Portfolio")

    def create_sample_ibkr_csv(self):
        """Create a sample IBKR CSV file for testing."""
        csv_content = '''Statement,Header,Field Name,Field Value
Statement,Data,Account,U1234567
Statement,Data,Period,"January 1, 2024 - December 31, 2024"
Statement,Data,WhenGenerated,"2024-12-31, 10:30:00 EST"
Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,Realized P/L,MTM P/L,Code
Trades,Data,Order,Stocks,USD,AAPL,2024-01-15 09:30:00,100,150.50,150.50,-15050,-1.00,-15051.00,0,0,O
Trades,Data,Order,Stocks,USD,GOOGL,2024-01-20 10:15:00,50,2800.00,2800.00,-140000,-2.50,-140002.50,0,0,O
Trades,Data,Order,Stocks,USD,AAPL,2024-06-15 14:30:00,-50,175.25,175.25,8762.50,-1.00,8761.50,1211.50,0,C
Trades,Data,SubTotal,,USD,,,,,,-213287.50,-4.50,-213292.00,1211.50,,
Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,USD,2024-03-15,AAPL(US0378331005) Cash Dividend USD 0.24 per Share (Ordinary Dividend),24.00
Dividends,Data,USD,2024-06-15,AAPL(US0378331005) Cash Dividend USD 0.25 per Share (Ordinary Dividend),12.50
Dividends,Data,USD,2024-09-15,GOOGL(US02079K3059) Cash Dividend USD 0.20 per Share (Ordinary Dividend),10.00
Dividends,Data,Total,,USD,46.50
Open Positions,Header,DataDiscriminator,Asset Category,Currency,Symbol,Quantity,Mult,Cost Price,Cost Basis,Close Price,Value,Unrealized P/L,Code
Open Positions,Data,Summary,Stocks,USD,AAPL,50,1,150.50,7525.00,175.25,8762.50,1237.50,
Open Positions,Data,Summary,Stocks,USD,GOOGL,50,1,2800.00,140000.00,2850.00,142500.00,2500.00,
Open Positions,Data,Total,,,,,,,147525.00,,151262.50,3737.50,'''

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write(csv_content)
        temp_file.close()
        return temp_file.name

    def test_import_ibkr_csv_data(self):
        """Test importing IBKR CSV data into portfolio."""
        # Create sample CSV file
        csv_file = self.create_sample_ibkr_csv()
        
        try:            # Parse IBKR CSV
            parser = IbkrCsvParser(logger=MockLogger())
            parser.parse(csv_file)

            # Verify parser extracted data correctly
            self.assertEqual(len(parser.trades), 3)  # 3 trade entries (excluding subtotal)
            self.assertEqual(len(parser.dividends), 3)  # 3 dividend entries (excluding total)
            self.assertEqual(len(parser.positions), 2)  # 2 position entries (excluding total)
             # Import into portfolio
            success = self.service.import_from_ibkr(
                self.portfolio.id,
                parser.trades,
                parser.dividends,
                parser.positions
            )
            self.assertTrue(success)

            # Verify activity entries were created (this is the main thing we care about)
            all_entries = self.service.get_activity_entries(self.portfolio.id)
            self.assertEqual(len(all_entries), 6)  # 3 trades + 3 dividends

            trade_entries = self.service.get_activity_entries(self.portfolio.id, activity_type='TRADE')
            dividend_entries = self.service.get_activity_entries(self.portfolio.id, activity_type='DIVIDEND')

            self.assertEqual(len(trade_entries), 3)
            self.assertEqual(len(dividend_entries), 3)
            
            # Verify stocks were created
            aapl_stock = self.equity_repo.find_by_symbol('AAPL', 'NASDAQ')
            googl_stock = self.equity_repo.find_by_symbol('GOOGL', 'NASDAQ')
            self.assertIsNotNone(aapl_stock)
            self.assertIsNotNone(googl_stock)
            
            # Verify trade data integrity
            aapl_trades = [e for e in trade_entries if e.stock_id == aapl_stock.id]
            googl_trades = [e for e in trade_entries if e.stock_id == googl_stock.id]
            
            self.assertEqual(len(aapl_trades), 2)  # Buy and sell
            self.assertEqual(len(googl_trades), 1)  # Buy only
            
            # Check specific trade amounts
            aapl_buy = next(e for e in aapl_trades if e.amount == Decimal('-15050'))
            aapl_sell = next(e for e in aapl_trades if e.amount == Decimal('8762.50'))
            googl_buy = googl_trades[0]
            
            self.assertEqual(aapl_buy.raw_data['quantity'], Decimal('100'))
            self.assertEqual(aapl_sell.raw_data['quantity'], Decimal('-50'))
            self.assertEqual(googl_buy.amount, Decimal('-140000'))
            
            # Verify dividend data
            aapl_dividends = [e for e in dividend_entries if 'AAPL' in e.raw_data.get('description', '')]
            googl_dividends = [e for e in dividend_entries if 'GOOGL' in e.raw_data.get('description', '')]
            
            self.assertEqual(len(aapl_dividends), 2)  # Two AAPL dividends
            self.assertEqual(len(googl_dividends), 1)  # One GOOGL dividend
            
            # Check dividend amounts
            aapl_div_amounts = [e.amount for e in aapl_dividends]
            self.assertIn(Decimal('24.00'), aapl_div_amounts)
            self.assertIn(Decimal('12.50'), aapl_div_amounts)
            self.assertEqual(googl_dividends[0].amount, Decimal('10.00'))

            # Verify holdings were created from positions data
            holdings = self.service.get_equity_holdings(self.portfolio.id)
            self.assertEqual(len(holdings), 2)  # AAPL and GOOGL holdings
            
            # Check specific holding details
            aapl_holding = next((h for h in holdings if self.equity_repo.get(h.equity_id).symbol == 'AAPL'), None)
            googl_holding = next((h for h in holdings if self.equity_repo.get(h.equity_id).symbol == 'GOOGL'), None)
            
            self.assertIsNotNone(aapl_holding)
            self.assertIsNotNone(googl_holding)
            self.assertEqual(aapl_holding.quantity, Decimal('50'))
            self.assertEqual(aapl_holding.cost_basis, Decimal('7525.00'))
            self.assertEqual(googl_holding.quantity, Decimal('50'))
            self.assertEqual(googl_holding.cost_basis, Decimal('140000.00'))

        finally:
            # Clean up temporary file
            os.unlink(csv_file)

    def test_import_ibkr_with_service_validation(self):
        """Test that IBKR import through service maintains domain invariants."""
        csv_file = self.create_sample_ibkr_csv()
        
        try:
            parser = IbkrCsvParser(logger=MockLogger())
            parser.parse(csv_file)
            
            # Import data
            self.service.import_from_ibkr(
                self.portfolio.id,
                parser.trades,
                parser.dividends,
                parser.positions
            )
            
            # Try to add a duplicate holding manually (should fail)
            from domain.portfolio.portfolio_errors import DuplicateHoldingError
            with self.assertRaises(DuplicateHoldingError):
                self.service.add_holding(
                    self.portfolio.id,
                    'AAPL',
                    Decimal('25'),
                    Decimal('4000.00')
                )
            
            # Verify that adding holdings for non-existing stocks works
            new_holding = self.service.add_holding(
                self.portfolio.id,
                'MSFT',
                Decimal('100'),
                Decimal('30000.00')
            )
            self.assertIsNotNone(new_holding)
            
            # Verify MSFT stock was created
            msft_stock = self.equity_repo.find_by_symbol('MSFT', 'NASDAQ')
            self.assertIsNotNone(msft_stock)

        finally:
            os.unlink(csv_file)

    def test_portfolio_service_with_ibkr_metadata(self):
        """Test that portfolio service properly handles IBKR metadata."""
        csv_file = self.create_sample_ibkr_csv()
        
        try:
            parser = IbkrCsvParser(logger=MockLogger())
            parser.parse(csv_file)
            
            # Verify parser metadata
            meta = parser.meta
            self.assertEqual(meta['Account'], 'U1234567')
            self.assertIn('Period', meta)
            self.assertIn('WhenGenerated', meta)
            
            # Import data and verify raw_data contains metadata
            self.service.import_from_ibkr(
                self.portfolio.id,
                parser.trades,
                parser.dividends,
                parser.positions
            )
            
            entries = self.service.get_activity_entries(self.portfolio.id)
            
            # Check that raw_data is properly preserved
            trade_entry = next(e for e in entries if e.activity_type == 'TRADE')
            self.assertIn('symbol', trade_entry.raw_data)
            self.assertIn('quantity', trade_entry.raw_data)
            self.assertIn('proceeds', trade_entry.raw_data)
            
            dividend_entry = next(e for e in entries if e.activity_type == 'DIVIDEND')
            self.assertIn('description', dividend_entry.raw_data)
            self.assertIn('amount', dividend_entry.raw_data)

        finally:
            os.unlink(csv_file)

    def test_import_nonexistent_portfolio_fails(self):
        """Test that importing to non-existent portfolio fails gracefully."""
        csv_file = self.create_sample_ibkr_csv()
        
        try:
            parser = IbkrCsvParser(logger=MockLogger())
            parser.parse(csv_file)
            
            # Try to import to non-existent portfolio
            success = self.service.import_from_ibkr(
                uuid4(),  # Non-existent portfolio
                parser.trades,
                parser.dividends,
                parser.positions
            )
            self.assertFalse(success)
            
        finally:
            os.unlink(csv_file)

if __name__ == '__main__':
    unittest.main()
