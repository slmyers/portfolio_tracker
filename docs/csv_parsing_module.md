# CSV Parsing Module Design

## Overview
This document outlines the design for a reusable CSV parsing module for the portfolio tracker project. The module is intended to provide a robust, extensible, and type-safe interface for parsing CSV files from various sources, supporting both simple and complex (multi-section) CSV formats.

## Goals
- Provide a generic, reusable interface for parsing CSV files
- Support custom row/section handlers for different CSV structures
- Integrate with dependency injection and separation of concerns principles
- Allow for strong type checking and validation
- Support streaming/large file parsing
- Enable easy extension for new CSV formats (e.g., IBKR, other brokers)

## Architecture
-
### Section Boundary Detection
- For multi-section CSVs, section boundaries are typically indicated by:
    - Section header lines (e.g., "Trades", "Dividends", etc.)
    - Blank lines separating sections
    - Special marker lines (e.g., lines with dashes or a specific format)
- The parser can be configured with a list of known section names or custom patterns to detect section starts.
- For new or custom formats, users can extend the detection logic by providing their own section marker detection function or configuration.
- `CsvParser` class: Core parser that reads CSV files, detects section boundaries, reads headers, and delegates row/section handling
- `CsvSectionHandler` interface: For handling specific sections or row types
- Pluggable validators and type converters
- Error handling and reporting

### Header Handling
- For single-section CSVs, the parser reads the first non-empty line as the header and maps each subsequent row to a dictionary using these headers as keys.
- For multi-section CSVs, the parser detects section boundaries, reads the section-specific header row, and uses it for all rows in that section until the next section begins. Each section handler receives rows as dictionaries with the appropriate keys for that section.

## Example Usage
```python
from core.csv import CsvParser, CsvSectionHandler

class MySectionHandler(CsvSectionHandler):
    def handle_row(self, row: dict):
        # process row
        pass

# Multi-section CSV example
parser = CsvParser(section_handlers={
    'Trades': MySectionHandler(),
    'Dividends': MySectionHandler(),
})
parser.parse('activity.csv')

# Single-section CSV example
parser = CsvParser(section_handlers={
    None: MySectionHandler(),  # Use None or a default key for single-section CSVs
})
parser.parse('simple.csv')
```

## Key Features
- Section-aware parsing (for multi-section CSVs)
- Customizable row and section handlers
- Type-safe row mapping (using dataclasses or TypedDict)
- Streaming support for large files
- Integration with dependency injection

## Extensibility
- New CSV formats can be supported by implementing new section handlers
- Validators and converters can be injected or configured

## Error Handling
- Collect and report parsing errors with context (row number, section, etc.)
- Optionally support strict and lenient modes

---
Update this document as the CSV parsing module evolves.
