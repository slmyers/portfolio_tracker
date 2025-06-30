# CSV Parsing Module Design

## Overview
This document outlines the design for a reusable CSV parsing module for the portfolio tracker project. The module is intended to provide a robust, extensible, and type-safe interface for parsing CSV files from various sources, supporting both simple and complex (multi-section) CSV formats.

All CSV parsers should be implemented in the `core/csv/` folder. The `BaseCSVParser` class in `core/csv/base.py` provides a common interface and utilities for all specialized CSV parsers (e.g., IBKR, other brokers). Specialized parsers should inherit from this base class for consistency and code reuse.

## Goals
- Provide a generic, reusable interface for parsing CSV files
- Support custom row/section handlers for different CSV structures
- Integrate with dependency injection and separation of concerns principles
- Allow for strong type checking and validation
- Support streaming/large file parsing
- Enable easy extension for new CSV formats (e.g., IBKR, other brokers)

## Architecture
- `BaseCSVParser` class in `core/csv/base.py`: Provides the core CSV parsing interface and utilities.
- Specialized parsers (e.g., `IbkrCsvParser` in `core/csv/ibkr.py`) inherit from `BaseCSVParser` and implement format-specific logic.
- Section handler classes (e.g., `CsvSectionHandler`) for handling specific sections or row types.
- Pluggable validators and type converters.
- Error handling and reporting.

### Section Boundary Detection
- For multi-section CSVs, section boundaries are typically indicated by:
    - Section header lines (e.g., "Trades", "Dividends", etc.)
    - Blank lines separating sections
    - Special marker lines (e.g., lines with dashes or a specific format)
- The parser can be configured with a list of known section names or custom patterns to detect section starts.
- For new or custom formats, users can extend the detection logic by providing their own section marker detection function or configuration.

### Header Handling
- For single-section CSVs, the parser reads the first non-empty line as the header and maps each subsequent row to a dictionary using these headers as keys.
- For multi-section CSVs, the parser detects section boundaries, reads the section-specific header row, and uses it for all rows in that section until the next section begins. Each section handler receives rows as dictionaries with the appropriate keys for that section.

## Example Usage

```python
from core.csv.base import BaseCSVParser, CsvSectionHandler

class MySectionHandler(CsvSectionHandler):
    def handle_row(self, row: dict):
        # process row
        pass

class MyLogger:
    def debug(self, msg, *a, **kw):
        print(msg)
    def info(self, msg, *a, **kw):
        print(msg)
    def warning(self, msg, *a, **kw):
        print(msg)

# Example of a custom parser inheriting from BaseCSVParser
class MyCustomCsvParser(BaseCSVParser):
    pass  # Implement format-specific logic as needed

# Multi-section CSV example
parser = MyCustomCsvParser(section_handlers={
    'Trades': MySectionHandler(),
    'Dividends': MySectionHandler(),
}, logger=MyLogger())
parser.parse('activity.csv')

# Single-section CSV example
parser = MyCustomCsvParser(section_handlers={
    None: MySectionHandler(),  # Use None or a default key for single-section CSVs
}, logger=MyLogger())
parser.parse('simple.csv')
```
## Logger Requirement

`BaseCSVParser` requires a `logger` argument for debug/info output. The logger must implement at least `debug`, `info`, and `warning` methods. All output is routed through this logger, supporting dependency injection and separation of concerns.

## Key Features
- Section-aware parsing (for multi-section CSVs)
- Customizable row and section handlers
- Type-safe row mapping (using dataclasses or TypedDict)
- Streaming support for large files
- Integration with dependency injection


## Extensibility
- New CSV formats can be supported by creating new parser classes that inherit from `BaseCSVParser`.
- Section handlers, validators, and converters can be injected or configured.

## Error Handling
- Collect and report parsing errors with context (row number, section, etc.)
- Optionally support strict and lenient modes

### Strict vs. Lenient Modes

The parser supports both strict and lenient error handling modes:

- **Strict mode:** Parsing will stop and raise an error as soon as a problem is encountered (e.g., missing required fields, type errors, unknown sections). This is useful for data pipelines where data quality is critical.
- **Lenient mode:** Parsing will continue even if errors are encountered. All errors and warnings are collected and made available for inspection after parsing. This is useful for exploratory analysis or when you want to process as much data as possible despite issues.

You can configure the desired mode via a parameter to the parser (e.g., `strict=True` or `strict=False`). The mode affects how the parser handles:
- Missing or extra fields
- Type conversion errors
- Unknown or malformed sections
- Any other row-level or section-level validation failures

Choose the mode that best fits your use case. See the parser’s API documentation for details on how to set the mode and retrieve error reports.

---
## Testing


For robust testing of the CSV parsing module, generate and use multiple synthetic test files. Store these in a directory such as `tests/test_data/` (see `tests/README.md` for naming conventions and coverage goals) and consider including:

- Minimal valid CSVs (smoke tests)
- Full-featured files with all possible sections and fields
- Edge cases (missing fields, extra columns, malformed rows)
- Files with only a subset of sections
- Files with unusual or rare data (e.g., multiple currencies, negative values, unknown codes)
- Very large files (for performance/streaming tests)

Name these files descriptively, reflecting their content and format (e.g., `minimal.csv`, `full.csv`, `edgecase.csv`, or format-specific names like `ibkr_activity.csv`, `otherbroker_positions.csv`). This ensures your tests are organized, maintainable, and provide good coverage for all expected and edge-case scenarios across different CSV formats.

Rows with a different number of columns than the header are considered malformed. The parser will raise or record an error for these cases, and this is covered by tests such as `bad_row_length.csv`.

---

## Injecting Normalizers and Validators

For maximum flexibility and testability, normalizers and validators should be injected into section handlers. This allows you to customize, reuse, or mock normalization and validation logic for different formats, environments, or tests.

For example:

```python
class TradesHandler:
    def __init__(self, date_normalizer, float_normalizer):
        self.date_normalizer = date_normalizer
        self.float_normalizer = float_normalizer

    def handle_row(self, row: dict):
        trade = {
            'date': self.date_normalizer(row['Date/Time']),
            'quantity': self.float_normalizer(row['Quantity']),
            # ...other normalization...
        }
```

You can then inject different normalizers as needed:

```python
handler = TradesHandler(date_normalizer=parse_ibkr_date, float_normalizer=float)
```

This approach keeps your code modular, testable, and highly configurable.

## Note on File Streaming

Currently, file streaming is not required for the supported CSV formats, as files are typically small enough to be read into memory. If streaming becomes necessary in the future (e.g., for very large files), streaming support will be implemented in the `BaseCSVParser` so that all format-specific parsers can benefit from it without code duplication.

---
Update this document as the CSV parsing module evolves or as new CSV formats are added.
