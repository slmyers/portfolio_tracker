"""
Tests for the CSV state machine implementation.
"""

import pytest
from unittest.mock import Mock
from core.csv.state_machine import (
    CsvStateMachine,
    TradesParsingState,
    DividendsParsingState,
    OpenPositionsParsingState,
    StatementParsingState,
    ForexBalancesParsingState,
    GenericParsingState,
    ParseState
)


class TestSectionParsingState:
    """Test the base section parsing state functionality."""
    
    def test_trades_parsing_state_skip_summary_rows(self):
        """Test that trades parsing state correctly identifies summary rows."""
        state = TradesParsingState("Trades")
        
        # Should skip total rows
        total_row = ["Trades", "Data", "Total", "100", "USD"]
        assert state.should_skip_row(total_row) is True
        
        # Should skip subtotal rows
        subtotal_row = ["Trades", "Data", "SubTotal", "50", "USD"]
        assert state.should_skip_row(subtotal_row) is True
        
        # Should not skip regular data rows
        data_row = ["Trades", "Data", "AAPL", "100", "USD"]
        assert state.should_skip_row(data_row) is False
    
    def test_dividends_parsing_state_skip_summary_rows(self):
        """Test that dividends parsing state correctly identifies summary rows."""
        state = DividendsParsingState("Dividends")
        
        # Should skip total rows
        total_row = ["Dividends", "Data", "Total", "100.00"]
        assert state.should_skip_row(total_row) is True
        
        # Should not skip regular data rows
        data_row = ["Dividends", "Data", "AAPL Dividend", "2.50"]
        assert state.should_skip_row(data_row) is False
    
    def test_statement_parsing_state_never_skips(self):
        """Test that statement parsing state never skips rows."""
        state = StatementParsingState("Statement")
        
        # Should never skip any rows
        any_row = ["Statement", "Data", "Field", "Value"]
        assert state.should_skip_row(any_row) is False
    
    def test_process_header(self):
        """Test header processing."""
        logger = Mock()
        state = TradesParsingState("Trades", logger)
        
        header_row = ["Trades", "Header", "Symbol", "Quantity", "Price"]
        state.process_header(header_row)
        
        assert state.header == ["Symbol", "Quantity", "Price"]
        assert state.normalized_header == ["symbol", "quantity", "price"]
        assert state.state == ParseState.HEADER
        logger.debug.assert_called_once()
    
    def test_process_data_row_without_header(self):
        """Test processing data row when no header is set."""
        logger = Mock()
        state = TradesParsingState("Trades", logger)
        handler = Mock()
        
        data_row = ["Trades", "Data", "AAPL", "100", "150.00"]
        state.process_data_row(data_row, handler)
        
        # Should log warning and not process the row
        logger.warning.assert_called_once()
        handler.handle_row.assert_not_called()
    
    def test_process_data_row_with_header(self):
        """Test processing data row with header set."""
        logger = Mock()
        state = TradesParsingState("Trades", logger)
        handler = Mock()
        
        # Set up header first
        header_row = ["Trades", "Header", "Symbol", "Quantity", "Price"]
        state.process_header(header_row)
        
        # Process data row
        data_row = ["Trades", "Data", "AAPL", "100", "150.00"]
        state.process_data_row(data_row, handler)
        
        # Should call handler with normalized data
        expected_data = {"symbol": "AAPL", "quantity": "100", "price": "150.00"}
        handler.handle_row.assert_called_once_with(expected_data)
        assert state.state == ParseState.DATA
    
    def test_process_data_row_skip_summary(self):
        """Test that summary rows are skipped."""
        logger = Mock()
        state = TradesParsingState("Trades", logger)
        handler = Mock()
        
        # Set up header first
        header_row = ["Trades", "Header", "Symbol", "Quantity", "Price"]
        state.process_header(header_row)
        
        # Process summary row
        summary_row = ["Trades", "Data", "Total", "1000", "15000.00"]
        state.process_data_row(summary_row, handler)
        
        # Should log debug message and not call handler
        logger.debug.assert_called()
        handler.handle_row.assert_not_called()
    
    def test_process_data_row_length_mismatch(self):
        """Test handling of data row with length mismatch."""
        logger = Mock()
        state = TradesParsingState("Trades", logger)
        handler = Mock()
        
        # Set up header first
        header_row = ["Trades", "Header", "Symbol", "Quantity", "Price"]
        state.process_header(header_row)
        
        # Process data row with wrong number of columns
        data_row = ["Trades", "Data", "AAPL", "100"]  # Missing price
        state.process_data_row(data_row, handler)
        
        # Should log warning and not call handler
        logger.warning.assert_called()
        handler.handle_row.assert_not_called()


class TestStatementParsingState:
    """Test the statement-specific parsing state."""
    
    def test_statement_process_row(self):
        """Test statement row processing."""
        logger = Mock()
        state = StatementParsingState("Statement", logger)
        handler = Mock()
        
        # Process statement data row
        row = ["Statement", "Data", "Account", "U12345"]
        state.process_row(row, handler)
        
        expected_data = {"field_name": "Account", "field_value": "U12345"}
        handler.handle_row.assert_called_once_with(expected_data)
    
    def test_statement_process_row_insufficient_columns(self):
        """Test statement row processing with insufficient columns."""
        logger = Mock()
        state = StatementParsingState("Statement", logger)
        handler = Mock()
        
        # Process row with insufficient columns
        row = ["Statement", "Data", "Account"]  # Missing value
        state.process_row(row, handler)
        
        # Should not call handler
        handler.handle_row.assert_not_called()


class TestOpenPositionsParsingState:
    """Test the open positions-specific parsing state."""

    def test_open_positions_skip_summary_rows(self):
        """Test that open positions parsing state correctly identifies summary rows."""
        state = OpenPositionsParsingState("Open Positions")

        # Should skip total rows
        total_row = ["Open Positions", "Data", "Total", "100", "USD"]
        assert state.should_skip_row(total_row) is True

        # Should skip subtotal rows
        subtotal_row = ["Open Positions", "Data", "SubTotal", "50", "USD"]
        assert state.should_skip_row(subtotal_row) is True

        # Should not skip regular data rows
        data_row = ["Open Positions", "Data", "AAPL", "100", "USD"]
        assert state.should_skip_row(data_row) is False


class TestForexBalancesParsingState:
    """Test the forex balances-specific parsing state."""

    def test_forex_balances_skip_summary_rows(self):
        """Test that forex balances parsing state correctly identifies summary rows."""
        state = ForexBalancesParsingState("Forex Balances")

        # Should skip total rows
        total_row = ["Forex Balances", "Data", "Total", "100", "USD"]
        assert state.should_skip_row(total_row) is True

        # Should skip subtotal rows
        subtotal_row = ["Forex Balances", "Data", "SubTotal", "50", "USD"]
        assert state.should_skip_row(subtotal_row) is True

        # Should not skip regular data rows
        data_row = ["Forex Balances", "Data", "EUR", "100", "USD"]
        assert state.should_skip_row(data_row) is False


class TestCsvStateMachine:
    """Test the CSV state machine."""
    
    def test_initialization(self):
        """Test state machine initialization."""
        logger = Mock()
        machine = CsvStateMachine(logger)
        
        assert machine.logger is logger
        assert machine.current_state is None
        assert machine.current_section_name is None
        assert len(machine.states) == 5  # Known sections
    
    def test_transition_to_known_section(self):
        """Test transitioning to a known section."""
        logger = Mock()
        machine = CsvStateMachine(logger)
        
        machine.transition_to_section("Trades")
        
        assert isinstance(machine.current_state, TradesParsingState)
        assert machine.current_section_name == "Trades"
        logger.debug.assert_called_once()
    
    def test_transition_to_unknown_section(self):
        """Test transitioning to an unknown section."""
        logger = Mock()
        machine = CsvStateMachine(logger)
        
        machine.transition_to_section("Unknown Section")
        
        assert isinstance(machine.current_state, GenericParsingState)
        assert machine.current_section_name == "Unknown Section"
        logger.debug.assert_called_once()
    
    def test_process_section_without_state(self):
        """Test processing section when no state is set."""
        logger = Mock()
        machine = CsvStateMachine(logger)
        handler = Mock()
        
        rows = [["Section", "Data", "value"]]
        machine.process_section(rows, handler)
        
        # Should log warning
        logger.warning.assert_called_once()
    
    def test_process_section_with_state(self):
        """Test processing section with state set."""
        logger = Mock()
        machine = CsvStateMachine(logger)
        handler = Mock()
        
        # Set up state
        machine.transition_to_section("Trades")
        
        # Mock the state's process_row method
        machine.current_state.process_row = Mock()
        
        rows = [
            ["Trades", "Header", "Symbol", "Quantity"],
            ["Trades", "Data", "AAPL", "100"]
        ]
        machine.process_section(rows, handler)
        
        # Should call process_row for each row
        assert machine.current_state.process_row.call_count == 2


@pytest.fixture
def sample_csv_rows():
    """Sample CSV rows for testing."""
    return [
        ["Trades", "Header", "Symbol", "Quantity", "Price"],
        ["Trades", "Data", "AAPL", "100", "150.00"],
        ["Trades", "Data", "GOOGL", "50", "2500.00"],
        ["Trades", "Data", "Total", "150", "162500.00"],
    ]


def test_integration_trades_parsing(sample_csv_rows):
    """Integration test for trades parsing."""
    logger = Mock()
    machine = CsvStateMachine(logger)
    handler = Mock()
    
    machine.transition_to_section("Trades")
    machine.process_section(sample_csv_rows, handler)
    
    # Should have processed 2 data rows (skipping total)
    assert handler.handle_row.call_count == 2
    
    # Check the data that was passed to handler
    calls = handler.handle_row.call_args_list
    assert calls[0][0][0] == {"symbol": "AAPL", "quantity": "100", "price": "150.00"}
    assert calls[1][0][0] == {"symbol": "GOOGL", "quantity": "50", "price": "2500.00"}
