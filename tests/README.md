# Tests

This folder contains test cases for the portfolio tracker modules, including the IBKR CSV parser and generic CSV parser tests.

## Running tests

You can run all tests with:

```bash
pytest
```

## Test data

See `test_data/` for sample CSVs and other files used in tests.

## IBKR CSV Parser Test Scenarios

- Parsing trades, dividends, and open positions from a real IBKR CSV export.
- Ensures that trades, dividends, and positions are parsed as lists of dictionaries.
- Checks that at least one trade, one dividend, and one position are found in the sample file.
- Verifies that the pretty print method outputs all three sections.

## Generic CSV Parser Coverage Goals
- Minimal valid files (smoke tests)
- Multi-section files
- Malformed files (missing fields, extra columns, bad types)
- Row/header length mismatches (rows with too few or too many columns)
- Edge cases (unusual or rare data)
- Large files (for performance/streaming tests)

Add new files as new formats or edge cases are encountered.
