"""
Tests for the refactored IBKR CSV parser with state machine.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from core.csv.ibkr import IbkrCsvParser, SectionNames


class TestIbkrCsvParserStateIntegration:
    """Test the integration of state machine with IBKR parser."""
    
    def test_parser_initialization_with_state_machine(self):
        """Test that parser correctly initializes state machine."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        assert hasattr(parser, 'state_machine')
        assert parser.state_machine.logger is logger
    
    def test_parse_section_trades_uses_state_machine(self):
        """Test that trades parsing uses state machine."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        handler = Mock()
        
        # Mock state machine methods
        parser.state_machine.transition_to_section = Mock()
        parser.state_machine.process_section = Mock()
        
        rows = [["Trades", "Header", "Symbol"], ["Trades", "Data", "AAPL"]]
        parser._parse_section_trades(rows, handler)
        
        parser.state_machine.transition_to_section.assert_called_once_with(SectionNames.TRADES.value)
        parser.state_machine.process_section.assert_called_once_with(rows, handler)
    
    def test_parse_section_dividends_uses_state_machine(self):
        """Test that dividends parsing uses state machine."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        handler = Mock()
        
        parser.state_machine.transition_to_section = Mock()
        parser.state_machine.process_section = Mock()
        
        rows = [["Dividends", "Header", "Date"], ["Dividends", "Data", "2024-01-01"]]
        parser._parse_section_dividends(rows, handler)
        
        parser.state_machine.transition_to_section.assert_called_once_with(SectionNames.DIVIDENDS.value)
        parser.state_machine.process_section.assert_called_once_with(rows, handler)
    
    def test_parse_section_statement_with_metadata_processing(self):
        """Test that statement parsing uses state machine and processes metadata."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        # Create a mock handler with statement_metadata
        handler = Mock()
        handler.statement_metadata = {
            "Period": '"January 1, 2024 - December 31, 2024"',
            "WhenGenerated": "2024-12-31, 23:59:59"
        }
        
        parser.state_machine.transition_to_section = Mock()
        parser.state_machine.process_section = Mock()
        parser._process_statement_metadata = Mock()
        
        rows = [["Statement", "Data", "Account", "U12345"]]
        parser._parse_section_statement(rows, handler)
        
        parser.state_machine.transition_to_section.assert_called_once_with(SectionNames.STATEMENT.value)
        parser.state_machine.process_section.assert_called_once_with(rows, handler)
        parser._process_statement_metadata.assert_called_once_with(handler)
    
    def test_parse_section_generic_uses_state_machine(self):
        """Test that generic parsing uses state machine."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        handler = Mock()
        
        # Set current section name on state machine
        parser.state_machine.current_section_name = "Unknown Section"
        parser.state_machine.transition_to_section = Mock()
        parser.state_machine.process_section = Mock()
        
        rows = [["Unknown", "Header", "Field"], ["Unknown", "Data", "Value"]]
        parser._parse_section_generic(rows, handler)
        
        parser.state_machine.transition_to_section.assert_called_once_with("Unknown Section")
        parser.state_machine.process_section.assert_called_once_with(rows, handler)
    
    def test_process_statement_metadata(self):
        """Test statement metadata processing."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        handler = Mock()
        handler.statement_metadata = {
            "Period": '"January 1, 2024 - December 31, 2024"',
            "WhenGenerated": "2024-12-31, 23:59:59"
        }
        
        parser._process_statement_metadata(handler)
        
        # Check that period was parsed
        meta = handler.statement_metadata
        assert "PeriodStart" in meta
        assert "PeriodEnd" in meta
        assert "GeneratedAt" in meta
    
    def test_parse_period_success(self):
        """Test successful period parsing."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        meta = {"Period": '"January 1, 2024 - December 31, 2024"'}
        parser._parse_period(meta)
        
        assert "PeriodStart" in meta
        assert "PeriodEnd" in meta
        assert str(meta["PeriodStart"]) == "2024-01-01"
        assert str(meta["PeriodEnd"]) == "2024-12-31"
    
    def test_parse_period_failure(self):
        """Test period parsing with invalid format."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        meta = {"Period": "Invalid format"}
        parser._parse_period(meta)
        
        # Should not have parsed dates, original value should remain
        assert meta["Period"] == "Invalid format"
    
    def test_parse_generated_date_success(self):
        """Test successful generated date parsing."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        meta = {"WhenGenerated": "2024-12-31, 23:59:59"}
        parser._parse_generated_date(meta)
        
        assert "GeneratedAt" in meta
        assert str(meta["GeneratedAt"]) == "2024-12-31 00:00:00"
    
    def test_parse_generated_date_failure(self):
        """Test generated date parsing with invalid format."""
        logger = Mock()
        parser = IbkrCsvParser(logger=logger)
        
        meta = {"WhenGenerated": "Invalid date"}
        parser._parse_generated_date(meta)
        
        # Should fall back to original value
        assert meta["GeneratedAt"] == "Invalid date"


@pytest.fixture
def sample_ibkr_csv_content():
    """Sample IBKR CSV content for testing."""
    return """Statement,Header,Field Name,Field Value
Statement,Data,Account,U12345678
Statement,Data,Period,"January 1, 2024 - December 31, 2024"
Statement,Data,WhenGenerated,"2024-12-31, 23:59:59"

Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,Realized P/L,MTM P/L,Code
Trades,Data,Order,Stocks,USD,AAPL,2024-01-15 09:30:00,100,150.00,150.00,-15000.00,1.00,15001.00,0,0,O
Trades,Data,Order,Stocks,USD,GOOGL,2024-01-20 10:00:00,10,2500.00,2500.00,-25000.00,1.00,25001.00,0,0,O
Trades,Data,SubTotal,,USD,,,110,,,,-40000.00,2.00,40002.00,0,0,
Trades,Data,Total,,USD,,,110,,,,-40000.00,2.00,40002.00,0,0,

Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,USD,2024-03-15,AAPL Cash Dividend,50.00
Dividends,Data,USD,2024-06-15,AAPL Cash Dividend,55.00
Dividends,Data,Total,,,105.00
"""


def test_full_parsing_integration(sample_ibkr_csv_content):
    """Integration test for full CSV parsing with state machine."""
    logger = Mock()
    parser = IbkrCsvParser(logger=logger)
    
    with patch("builtins.open", mock_open(read_data=sample_ibkr_csv_content)):
        result = parser.parse("test.csv")
    
    # Check that we got the expected data
    assert len(result.trades) == 2  # Two trade entries (excluding subtotal/total)
    assert len(result.dividends) == 2  # Two dividend entries (excluding total)
    assert len(result.meta) > 0  # Statement metadata
    
    # Check trade data
    first_trade = result.trades[0]
    assert first_trade["symbol"] == "AAPL"
    assert first_trade["quantity"] == 100.0
    assert first_trade["t_price"] == 150.0  # Now should work with corrected field mapping
    
    # Check dividend data
    first_dividend = result.dividends[0]
    assert first_dividend["description"] == "AAPL Cash Dividend"
    assert first_dividend["amount"] == 50.0
    
    # Check metadata
    meta = result.meta
    assert meta["Account"] == "U12345678"
    assert "PeriodStart" in meta
    assert "PeriodEnd" in meta
