# CSV Parser Test Data

This directory contains synthetic CSV files for testing the base and specialized CSV parsers. 

## Naming Convention
- Use descriptive names reflecting the content and format:
  - `simple.csv`: Minimal valid single-section CSV
  - `multisection.csv`: Multi-section CSV with headers and data
  - `malformed.csv`: CSV with missing fields, bad types, or malformed rows
  - `edgecase.csv`: CSV with edge cases (empty, negative, zero, large values)

## Coverage Goals
- Minimal valid files (smoke tests)
- Multi-section files
- Malformed files (missing fields, extra columns, bad types)
- Edge cases (unusual or rare data)
- Large files (for performance/streaming tests)

Add new files as new formats or edge cases are encountered.
