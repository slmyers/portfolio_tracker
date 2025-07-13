# Debugging and Resolving Issues in IBKR CSV Import

## Issue 1: Incorrect Currency in Dividend Activity Report Entries
### Problem
Dividend events in the `activity_report_entry` table are recorded in USD, but the raw data shows CAD.

### Suspected Root Cause
The `IbkrCsvParser` or the `PortfolioService` may be defaulting to USD when parsing or saving dividend entries, instead of using the currency specified in the raw data.

### Debugging Strategy
1. **Inspect the Parser**:
   - Review the `IbkrCsvParser` implementation, specifically the `_parse_section_dividends` method, to ensure it correctly extracts the `currency` field.
   - Verify that the `currency` field is passed to the `PortfolioService.add_activity_entry` method.

2. **Inspect the Service Layer**:
   - Check the `PortfolioService.add_activity_entry` method to ensure it uses the `currency` field from the parsed data when creating `ActivityReportEntry` objects.

3. **Database Validation**:
   - Query the `activity_report_entry` table to confirm the stored `currency` values match the raw data.

### Unit Test
```python
def test_dividend_parsing():
    csv_content = '''Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,CAD,2025-01-03,XAW(CA46435D1096) Cash Dividend CAD 0.39601 per Share (Ordinary Dividend),25.34
Dividends,Data,USD,2025-03-28,QQQM(US46138G6492) Cash Dividend USD 0.31763 per Share (Ordinary Dividend),4.13
'''
    parser = IbkrCsvParser(logger=MockLogger())
    parser.parse(csv_content)

    # Verify parsed dividends
    assert len(parser.dividends) == 2
    assert parser.dividends[0]['currency'] == 'CAD'
    assert parser.dividends[0]['amount'] == 25.34
    assert parser.dividends[1]['currency'] == 'USD'
    assert parser.dividends[1]['amount'] == 4.13
```

---

## Issue 2: Missing Forex Balances in Cash Holdings
### Problem
The `cash_holding` table shows 0 CAD and 0 USD balances, but the "Forex Balances" section in the CSV contains valid data.

### Suspected Root Cause
The `IbkrCsvParser` does not handle the "Forex Balances" section, or the `PortfolioService.import_from_ibkr` method does not process forex data into cash holdings.

### Debugging Strategy
1. **Parser Validation**:
   - Check if the `IbkrCsvParser` has a handler for the "Forex Balances" section.
   - If missing, implement a `_parse_section_forex_balances` method to extract forex data.

2. **Service Layer Validation**:
   - Ensure the `PortfolioService.import_from_ibkr` method processes forex data and updates the `cash_holding` repository.

3. **Database Validation**:
   - Query the `cash_holding` table to confirm balances are updated after import.

### Unit Test
```python
def test_forex_balances_parsing():
    csv_content = '''Forex Balances,Header,Asset Category,Currency,Description,Quantity,Cost Price,Cost Basis in CAD,Close Price,Value in CAD,Unrealized P/L in CAD,Code
Forex Balances,Data,Forex,CAD,CAD,72.611174145,0,-72.611174145,1,72.611174145,0,
Forex Balances,Data,Forex,CAD,USD,37.1525,1.40358455,-52.146675,1.368,50.82462,-1.322055,
'''
    parser = IbkrCsvParser(logger=MockLogger())
    parser.parse(csv_content)

    # Verify parsed forex balances
    assert len(parser.forex_balances) == 2
    assert parser.forex_balances[0]['currency'] == 'CAD'
    assert parser.forex_balances[0]['quantity'] == 72.611174145
    assert parser.forex_balances[1]['currency'] == 'USD'
    assert parser.forex_balances[1]['quantity'] == 37.1525
```

---

## Issue 3: Mislabeling Portfolio ID as Tenant ID - RESOLVED ✅
### Problem
The `portfolio` table uses the input `portfolio_id` as the `tenant_id`, but the command should accept separate `portfolio_id` and `tenant_id` inputs.

### Solution Implemented
1. **Command Enhancement**: 
   - Updated `import_ibkr_csv` command to accept both `--tenant-id` and `--portfolio-id` arguments
   - Fixed command usage documentation

2. **Service Enhancement**:
   - Modified `PortfolioService.create_portfolio` method to accept an optional `portfolio_id` parameter
   - Updated method signature: `create_portfolio(tenant_id, name, portfolio_id=None, conn=None)`
   - Ensures correct assignment of `tenant_id` and `portfolio_id` values

3. **Database Validation**:
   - Portfolio table now correctly stores separate `tenant_id` and `portfolio_id` values
   - Fixed the logic that was incorrectly using `portfolio_id` as `tenant_id`

### Unit Test - PASSING ✅
```python
def test_create_portfolio_with_tenant_id():
    tenant_id = uuid4()
    portfolio_id = uuid4()
    portfolio = PortfolioService.create_portfolio(
        tenant_id=tenant_id, 
        name="Test Portfolio", 
        portfolio_id=portfolio_id
    )
    assert portfolio.tenant_id == tenant_id
    assert portfolio.id == portfolio_id
    assert portfolio.tenant_id != portfolio.id  # They should be different
```

### Updated Usage
```bash
python -m commands.import_ibkr_csv \
    --tenant-id <tenant-uuid> \
    --portfolio-id <portfolio-uuid> \
    --portfolio-name "Portfolio Name" \
    --csv-file <path-to-csv>
```

---

## Summary of Changes - Issue 3 Resolved ✅
1. **Parser Enhancements**:
   - Add a `_parse_section_forex_balances` method to `IbkrCsvParser`. (Pending)

2. **Service Enhancements**:
   - Update `PortfolioService.import_from_ibkr` to handle forex balances. (Pending)
   - ✅ **COMPLETED**: `PortfolioService.create_portfolio` now distinguishes between `tenant_id` and `portfolio_id`.

3. **Command Enhancements**:
   - ✅ **COMPLETED**: Modified `import_ibkr_csv` to accept `--tenant-id` and `--portfolio-id` arguments.

4. **Unit Tests**:
   - Add tests for dividend parsing, forex balances parsing. (Pending)
   - ✅ **COMPLETED**: Added tests for portfolio creation with tenant ID.

**Issue 3 Status**: ✅ **RESOLVED** - Portfolio creation now correctly distinguishes between tenant_id and portfolio_id.
