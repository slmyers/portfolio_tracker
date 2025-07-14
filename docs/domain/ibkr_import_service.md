# IBKR Import Service

The `IBKRImportService` is a specialized service that coordinates the import of Interactive Brokers (IBKR) CSV data into portfolios. It was created as part of the PortfolioService refactor to provide comprehensive import functionality while coordinating between holdings and activity management.

## Overview

This service provides the single entry point for importing IBKR data, handling multiple data types (trades, dividends, positions, forex balances) in a coordinated manner. It ensures data consistency, provides detailed reporting, and handles error conditions gracefully.

## Architecture

The service orchestrates import operations by coordinating between:
- Portfolio validation and management
- Holdings management for positions and forex balances
- Activity management for trades and dividends
- Comprehensive error tracking and reporting

## Dependencies

The service requires:
- `PortfolioRepository` - Portfolio validation and management
- `HoldingsManagementService` - For positions and forex balance import
- `ActivityManagementService` - For trades and dividends import

## Core Method

### `import_from_ibkr(portfolio_id, trades=None, dividends=None, positions=None, forex_balances=None, conn=None)`

The main import method that handles comprehensive IBKR data import.

**Parameters:**
- `portfolio_id` (UUID): Target portfolio identifier
- `trades` (List[dict], optional): Trade transaction data
- `dividends` (List[dict], optional): Dividend payment data
- `positions` (List[dict], optional): Current position holdings
- `forex_balances` (List[dict], optional): Currency balance data
- `conn` (optional): Database connection for transactions

**Returns:** `ImportResult` object with detailed success/failure information

## Data Type Handling

### Trades Import

Processes trade transactions as activity entries:

**Expected Trade Format:**
```python
{
    'symbol': 'AAPL',
    'datetime': '2024-01-01T10:00:00',  # ISO format or "YYYY-MM-DD, HH:MM:SS"
    'proceeds': Decimal('1000.00'),
    'quantity': Decimal('10'),
    'commission': Decimal('5.00')
}
```

**Processing:**
- Creates activity entries with type "TRADE"
- Automatically creates equity entities for new symbols
- Handles multiple datetime formats
- Skips invalid trades with warnings

### Dividends Import

Processes dividend payments as activity entries:

**Expected Dividend Format:**
```python
{
    'description': 'AAPL Dividend',
    'date': '2024-01-15',
    'amount': Decimal('50.00'),
    'currency': 'USD'
}
```

**Processing:**
- Creates activity entries with type "DIVIDEND"
- Handles currency parsing and validation
- Supports various date formats
- Preserves original data in raw_data field

### Positions Import

Converts current positions to equity holdings:

**Expected Position Format:**
```python
{
    'symbol': 'AAPL',
    'quantity': 50,
    'cost_basis': 7525.00
}
```

**Processing:**
- Creates or updates equity holdings
- Automatically creates equity entities for new symbols
- Tracks new equity and holding creation
- Uses default exchange ("NASDAQ") if not specified

### Forex Balances Import

Imports currency balances as cash holdings:

**Expected Forex Format:**
```python
{
    'currency': 'USD',
    'quantity': 37.1525,
    'description': 'USD',
    'asset_category': 'Forex',
    'cost_price': 1.40358455,
    'value_in_cad': 50.82462
}
```

**Processing:**
- Creates or updates cash holdings for supported currencies
- Validates currency codes against Currency enum
- Tracks new cash holding creation
- Skips unsupported currencies with warnings

## Import Result

The service returns a comprehensive `ImportResult` object:

```python
@dataclass
class ImportResult:
    success: bool = True
    import_source: str = "IBKR_CSV"
    portfolio_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Success counts
    trades_imported: int = 0
    dividends_imported: int = 0
    positions_imported: int = 0
    forex_balances_imported: int = 0
    activity_entries_created: int = 0
    equity_holdings_created: int = 0
    equities_created: int = 0
    cash_holdings_created: int = 0
    
    # Error tracking
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    failed_items: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Skip tracking
    skipped_trades: int = 0
    skipped_positions: int = 0
```

## Features

### Comprehensive Error Handling

The service provides detailed error tracking:

**Portfolio Validation:**
```python
# Returns failure result for non-existent portfolio
result = service.import_from_ibkr(
    portfolio_id=uuid4(),  # Non-existent
    trades=[]
)
assert not result.success
assert result.error_type == "PortfolioNotFoundError"
```

**Individual Item Failures:**
```python
# Continues processing despite individual failures
trades = [
    {'symbol': 'AAPL', 'datetime': '2024-01-01T10:00:00', 'proceeds': 1000},
    {'proceeds': 500}  # Missing required fields
]

result = service.import_from_ibkr(portfolio_id, trades=trades)
assert result.success
assert result.trades_imported == 1
assert result.skipped_trades == 1
assert len(result.warnings) == 1
```

### Currency Validation

Handles currency validation gracefully:

```python
forex_balances = [
    {'currency': 'USD', 'quantity': 1000},  # Supported
    {'currency': 'CHF', 'quantity': 500}    # Unsupported
]

result = service.import_from_ibkr(portfolio_id, forex_balances=forex_balances)
assert result.forex_balances_imported == 1
assert "Unsupported currency 'CHF'" in result.warnings[0]
```

### Transaction Support

All import operations support database transactions:

```python
with db.transaction() as conn:
    result = service.import_from_ibkr(
        portfolio_id=portfolio.id,
        trades=trades,
        dividends=dividends,
        positions=positions,
        forex_balances=forex_balances,
        conn=conn
    )
    # All operations committed together or rolled back on failure
```

### Portfolio State Tracking

Updates portfolio import metadata:

```python
# Portfolio tracks import history
result = service.import_from_ibkr(portfolio_id, trades=trades)
portfolio = portfolio_repo.get(portfolio_id)
assert portfolio.last_import_source == "IBKR_CSV"
assert portfolio.last_import_count == result.activity_entries_created
```

## Usage Examples

### Basic Import

```python
# Create IBKR import service
ibkr_service = IBKRImportService(
    portfolio_repo=portfolio_repo,
    holdings_service=holdings_service,
    activity_service=activity_service
)

# Import trades only
result = ibkr_service.import_from_ibkr(
    portfolio_id=portfolio.id,
    trades=[
        {
            'symbol': 'AAPL',
            'datetime': '2024-01-01T10:00:00',
            'proceeds': Decimal('1000.00'),
            'quantity': Decimal('10'),
            'commission': Decimal('5.00')
        }
    ]
)

print(f"Imported {result.trades_imported} trades")
print(f"Created {result.activity_entries_created} activity entries")
```

### Comprehensive Import

```python
# Import all data types
result = ibkr_service.import_from_ibkr(
    portfolio_id=portfolio.id,
    trades=[
        {
            'symbol': 'AAPL',
            'datetime': '2024-01-01T10:00:00',
            'proceeds': Decimal('1000.00'),
            'quantity': Decimal('10'),
            'commission': Decimal('5.00')
        }
    ],
    dividends=[
        {
            'description': 'AAPL Dividend',
            'date': '2024-01-15',
            'amount': Decimal('50.00'),
            'currency': 'USD'
        }
    ],
    positions=[
        {
            'symbol': 'AAPL',
            'quantity': 50,
            'cost_basis': 7525.00
        }
    ],
    forex_balances=[
        {
            'currency': 'USD',
            'quantity': 1000.00,
            'description': 'USD',
            'asset_category': 'Forex'
        }
    ]
)

# Check comprehensive results
if result.success:
    print(f"Successfully imported:")
    print(f"  - {result.trades_imported} trades")
    print(f"  - {result.dividends_imported} dividends")
    print(f"  - {result.positions_imported} positions")
    print(f"  - {result.forex_balances_imported} forex balances")
    print(f"  - Created {result.activity_entries_created} activity entries")
    print(f"  - Created {result.equity_holdings_created} equity holdings")
    print(f"  - Created {result.equities_created} new equities")
    print(f"  - Created {result.cash_holdings_created} cash holdings")
else:
    print(f"Import failed: {result.error_message}")
```

### Error Handling

```python
# Handle import errors
result = ibkr_service.import_from_ibkr(
    portfolio_id=portfolio.id,
    trades=trades_with_issues
)

if not result.success:
    print(f"Import failed: {result.error_message}")
    print(f"Error type: {result.error_type}")

# Check warnings and skipped items
for warning in result.warnings:
    print(f"Warning: {warning}")

for failed_item in result.failed_items:
    print(f"Failed to import: {failed_item}")

print(f"Skipped {result.skipped_trades} trades due to errors")
```

## Data Format Support

### DateTime Handling

Supports multiple datetime formats:

```python
# ISO format
'datetime': '2024-01-01T10:00:00'

# IBKR CSV format
'datetime': '2024-01-01, 10:00:00'

# Automatic parsing
trade_datetime = parse_ibkr_datetime(trade['datetime'])
```

### Numeric Parsing

Handles various numeric formats:

```python
# Automatic decimal conversion
quantity = Decimal(str(position['quantity']))
cost_basis = Decimal(str(position.get('cost_basis', 0)))
```

### Currency Handling

Validates and processes currency codes:

```python
# Supported currencies: USD, CAD, EUR, GBP, JPY, AUD
if currency_str in Currency.__members__:
    currency = Currency(currency_str)
else:
    # Skip with warning
    result.add_warning(f"Unsupported currency '{currency_str}'")
```

## Testing

The service is thoroughly tested with comprehensive unit tests covering:
- Individual data type imports (trades, dividends, positions, forex)
- Comprehensive multi-type imports
- Error conditions and edge cases
- Currency validation and unsupported currencies
- Portfolio validation
- Skip logic for invalid data
- Transaction support
- Import result tracking

## Integration

This service is used by:
- `PortfolioService.import_from_ibkr()` method
- Direct integration for specialized import operations
- Batch import processes

## Error Recovery

The service is designed for resilient imports:
- Continues processing despite individual item failures
- Provides detailed tracking of successes and failures
- Allows for partial imports with warnings
- Supports retry logic for failed items

## Related Documentation

- [Portfolio Service](./portfolio_service.md)
- [Holdings Management Service](./holdings_management_service.md)
- [Activity Management Service](./activity_management_service.md)
- [Portfolio Domain Models](./portfolio_models.md)
- [IBKR CSV Import Guide](../csv_import_guide.md)
