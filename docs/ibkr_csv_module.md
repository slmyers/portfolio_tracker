# Interactive Brokers (IBKR) CSV Export Module Design

## Overview
This document outlines the design for a specialized module to parse and process Interactive Brokers (IBKR) activity report CSV exports. This module will leverage the generic CSV parsing module and provide IBKR-specific logic for section detection, row mapping, and data normalization.

## Goals
- Accurately parse IBKR activity report CSVs, including all relevant sections (Trades, Dividends, Interest, Fees, etc.)
- Normalize and validate data for downstream portfolio analysis
- Handle multi-section, multi-currency, and multi-account reports
- Integrate with dependency injection and the core CSV parsing module
- Provide strong type checking and error reporting

## Architecture
- `IbkrCsvParser` class: Extends or composes the generic `CsvParser`
- Section-specific handlers (e.g., `IbkrTradesHandler`, `IbkrDividendsHandler`)
- Data normalization utilities (e.g., currency conversion, symbol mapping)
- Error and warning reporting for malformed or unexpected data

## Example Usage
```python
from core.ibkr_csv import IbkrCsvParser, IbkrTradesHandler

# Example section handler for the "Trades" section
class IbkrTradesHandler:
    def __init__(self):
        self.trades = []

    def handle_row(self, row: dict):
        # Example: map and normalize row fields
        trade = {
            'date': row['Date/Time'],
            'symbol': row['Symbol'],
            'quantity': float(row['Quantity']),
            'price': float(row['T. Price']),
            'proceeds': float(row['Proceeds']),
        }
        self.trades.append(trade)

parser = IbkrCsvParser(section_handlers={
    'Trades': IbkrTradesHandler(),
    # Add other handlers as needed
})
activity = parser.parse('ibkr_activity.csv')
# activity.trades, activity.dividends, ...
```

## Key Features
- Section-aware parsing for IBKR's multi-section CSV format
- Typed row mapping for each section (using dataclasses or TypedDict)
- Data normalization (e.g., date/time, currency, symbol)
- Error and warning collection
- Extensible for new IBKR report formats or additional sections

## Extensibility
- New IBKR sections can be supported by adding new handlers
- Normalization and validation logic can be injected or configured

## Error Handling
- Detailed error and warning reporting with section and row context
- Optionally support strict and lenient parsing modes

---
Update this document as the IBKR CSV module evolves or as new report formats are encountered.
