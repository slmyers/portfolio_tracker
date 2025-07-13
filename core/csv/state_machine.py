"""
State machine implementation for CSV parsing.

This module provides a state machine abstraction for parsing multi-section CSV files,
where each section requires different parsing logic.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from core.csv.utils import normalize_field, is_summary_row


class ParseState(Enum):
    """Enum representing different parsing states."""
    INITIAL = "initial"
    HEADER = "header"
    DATA = "data"
    SECTION_END = "section_end"


class SectionParsingState(ABC):
    """
    Abstract base class for section-specific parsing states.
    
    Each CSV section (e.g., Trades, Dividends) should implement this interface
    to define how rows in that section should be processed.
    """
    
    def __init__(self, section_name: str, logger=None):
        self.section_name = section_name
        self.logger = logger
        self.state = ParseState.INITIAL
        self.header = None
        self.normalized_header = None
    
    @abstractmethod
    def should_skip_row(self, row: List[str]) -> bool:
        """
        Determine if a row should be skipped (e.g., summary rows).
        
        Args:
            row: CSV row as list of strings
            
        Returns:
            True if row should be skipped, False otherwise
        """
        pass
    
    def process_header(self, row: List[str]) -> None:
        """
        Process a header row.
        
        Args:
            row: Header row as list of strings
        """
        self.header = row[2:]  # Skip first two columns (section name, row type)
        self.normalized_header = [normalize_field(h) for h in self.header]
        self.state = ParseState.HEADER
        
        if self.logger:
            self.logger.debug(f"[IBKR DEBUG] Detected header in {self.section_name}: {self.header}")
    
    def process_data_row(self, row: List[str], handler) -> None:
        """
        Process a data row.
        
        Args:
            row: Data row as list of strings
            handler: Section handler to process the parsed data
        """
        if not self.header:
            if self.logger:
                self.logger.warning(f"[IBKR WARNING] Data row encountered before header in {self.section_name} section.")
            return
        
        if self.should_skip_row(row):
            if self.logger:
                self.logger.debug(f"[IBKR DEBUG] Skipping summary row in {self.section_name}: {row}")
            return
        
        data_row = row[2:]  # Skip first two columns
        if len(data_row) != len(self.header):
            if self.logger:
                self.logger.warning(f"[IBKR WARNING] Data/header length mismatch in {self.section_name}: {data_row} vs {self.header}")
            return
        
        data = dict(zip(self.normalized_header, data_row))
        handler.handle_row(data)
        self.state = ParseState.DATA
    
    def process_row(self, row: List[str], handler) -> None:
        """
        Process a CSV row based on its type.
        
        Args:
            row: CSV row as list of strings
            handler: Section handler to process the parsed data
        """
        if not any(cell.strip() for cell in row):
            return
        
        row_type = row[1].strip() if len(row) > 1 else None
        
        if row_type == 'Header':
            self.process_header(row)
        elif row_type == 'Data':
            self.process_data_row(row, handler)


class TradesParsingState(SectionParsingState):
    """Parsing state for Trades section."""
    
    def should_skip_row(self, row: List[str]) -> bool:
        return is_summary_row(row, summary_keywords=["total", "subtotal"])


class DividendsParsingState(SectionParsingState):
    """Parsing state for Dividends section."""
    
    def should_skip_row(self, row: List[str]) -> bool:
        return is_summary_row(row, summary_keywords=["total"])


class OpenPositionsParsingState(SectionParsingState):
    """Parsing state for Open Positions section."""
    
    def should_skip_row(self, row: List[str]) -> bool:
        return is_summary_row(row, summary_keywords=["total", "subtotal"])


class StatementParsingState(SectionParsingState):
    """Parsing state for Statement section."""
    
    def should_skip_row(self, row: List[str]) -> bool:
        return False  # Statement section doesn't have summary rows to skip
    
    def process_row(self, row: List[str], handler) -> None:
        """
        Statement section has a different structure, so we override the base implementation.
        """
        if len(row) >= 4 and row[1] == "Data":
            handler.handle_row({
                "field_name": row[2].strip(),
                "field_value": row[3].strip()
            })


class ForexBalancesParsingState(SectionParsingState):
    """Parsing state for Forex Balances section."""
    
    def should_skip_row(self, row: List[str]) -> bool:
        return is_summary_row(row, summary_keywords=["total"])


class GenericParsingState(SectionParsingState):
    """Generic parsing state for unknown sections."""
    
    def should_skip_row(self, row: List[str]) -> bool:
        return False  # Don't skip any rows for unknown sections


class CsvStateMachine:
    """
    State machine for parsing multi-section CSV files.
    
    This class manages the transition between different parsing states
    based on the section being processed.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        self.states = {
            "Trades": TradesParsingState("Trades", logger),
            "Dividends": DividendsParsingState("Dividends", logger),
            "Open Positions": OpenPositionsParsingState("Open Positions", logger),
            "Statement": StatementParsingState("Statement", logger),
            "Forex Balances": ForexBalancesParsingState("Forex Balances", logger),
        }
        self.current_state = None
        self.current_section_name = None
    
    def transition_to_section(self, section_name: str) -> None:
        """
        Transition to a new section parsing state.
        
        Args:
            section_name: Name of the section to transition to
        """
        if section_name in self.states:
            self.current_state = self.states[section_name]
            self.current_section_name = section_name
            if self.logger:
                self.logger.debug(f"[IBKR DEBUG] Transitioned to section: {section_name}")
        else:
            self.current_state = GenericParsingState(section_name, self.logger)
            self.current_section_name = section_name
            if self.logger:
                self.logger.debug(f"[IBKR DEBUG] Using generic parser for unknown section: {section_name}")
    
    def process_section(self, rows: List[List[str]], handler) -> None:
        """
        Process all rows in a section using the current state.
        
        Args:
            rows: List of CSV rows for the section
            handler: Section handler to process the parsed data
        """
        if not self.current_state:
            if self.logger:
                self.logger.warning("[IBKR WARNING] No current state set for processing rows")
            return
        
        for row in rows:
            self.current_state.process_row(row, handler)
