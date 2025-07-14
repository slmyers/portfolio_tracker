# Activity Management Service

The `ActivityManagementService` is a specialized service that handles all activity report entry operations within portfolios. It was created as part of the PortfolioService refactor to provide focused, testable functionality for activity tracking and management.

## Overview

This service provides a clean interface for managing activity report entries that track various portfolio activities such as trades, dividends, and other financial events. It handles the complexity of entity creation, currency parsing, and data validation while maintaining transaction support.

## Architecture

The service acts as a bridge between the application layer and domain repositories, coordinating operations across:
- Portfolio validation
- Equity creation and management (for trade activities)
- Activity entry creation and management
- Currency parsing and validation

## Dependencies

The service requires the following repository dependencies:
- `PortfolioRepository` - Portfolio validation and management
- `EquityRepository` - Equity/stock entity management for trade activities
- `ActivityReportEntryRepository` - Activity entry persistence

## Core Methods

### Activity Entry Management

#### `add_activity_entry(portfolio_id, activity_type, amount, date, stock_symbol=None, raw_data=None, conn=None)`

Creates a new activity report entry in the specified portfolio.

**Features:**
- Automatic equity creation for trade activities
- Portfolio validation
- Currency parsing from raw data
- Transaction support
- Flexible data handling

**Parameters:**
- `portfolio_id` (UUID): Target portfolio
- `activity_type` (str): Type of activity (e.g., "TRADE", "DIVIDEND")
- `amount` (Decimal): Activity amount
- `date` (datetime): Activity date
- `stock_symbol` (str, optional): Stock symbol for trade activities
- `raw_data` (dict, optional): Raw import data for reference
- `conn` (optional): Database connection for transactions

**Returns:** ActivityReportEntry object or None if failed

**Example:**
```python
# Trade activity
entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="TRADE",
    amount=Decimal('1000.00'),
    date=datetime.now(),
    stock_symbol="AAPL",
    raw_data={
        'symbol': 'AAPL',
        'quantity': 10,
        'commission': 5.00
    }
)

# Dividend activity
entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="DIVIDEND",
    amount=Decimal('50.00'),
    date=datetime.now(),
    raw_data={
        'description': 'AAPL Dividend',
        'currency': 'USD'
    }
)
```

#### `get_activity_entries(portfolio_id, activity_type=None, limit=100, offset=0, conn=None)`

Retrieves activity entries for a portfolio with optional filtering and pagination.

**Parameters:**
- `portfolio_id` (UUID): Portfolio identifier
- `activity_type` (str, optional): Filter by activity type
- `limit` (int): Maximum number of entries to return (default: 100)
- `offset` (int): Number of entries to skip (default: 0)
- `conn` (optional): Database connection

**Returns:** List of ActivityReportEntry objects

**Example:**
```python
# Get all activities
all_entries = service.get_activity_entries(portfolio.id)

# Get only trades
trade_entries = service.get_activity_entries(
    portfolio_id=portfolio.id,
    activity_type="TRADE"
)

# Get paginated results
recent_entries = service.get_activity_entries(
    portfolio_id=portfolio.id,
    limit=20,
    offset=0
)
```

## Features

### Automatic Equity Creation

For trade activities, the service automatically creates missing equity entities:

```python
# If "TSLA" doesn't exist as an equity, it will be created
entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="TRADE",
    amount=Decimal('5000.00'),
    date=datetime.now(),
    stock_symbol="TSLA"  # New symbol
)
```

### Currency Parsing

The service intelligently parses currency information from various sources:

**From raw_data:**
```python
entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="DIVIDEND",
    amount=Decimal('100.00'),
    date=datetime.now(),
    raw_data={
        'currency': 'CAD'  # Currency parsed from raw data
    }
)
```

**Explicit currency parameter:**
```python
entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="DIVIDEND",
    amount=Decimal('100.00'),
    date=datetime.now(),
    currency='EUR'  # Direct currency specification
)
```

**Default currency fallback:**
- Defaults to USD if no currency is specified
- Gracefully handles invalid currency codes

### Transaction Support

All methods support database transactions:

```python
with db.transaction() as conn:
    # Multiple activity entries in single transaction
    entry1 = service.add_activity_entry(
        portfolio.id, "TRADE", Decimal('1000'), datetime.now(), "AAPL", conn=conn
    )
    entry2 = service.add_activity_entry(
        portfolio.id, "DIVIDEND", Decimal('50'), datetime.now(), conn=conn
    )
```

### Flexible Data Handling

The service handles various data formats from different import sources:

**IBKR Trade Data:**
```python
ibkr_trade = {
    'symbol': 'AAPL',
    'datetime': '2024-01-01T10:00:00',
    'proceeds': 1000.00,
    'quantity': 10,
    'commission': 5.00
}

entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="TRADE",
    amount=Decimal(str(ibkr_trade['proceeds'])),
    date=datetime.fromisoformat(ibkr_trade['datetime']),
    stock_symbol=ibkr_trade['symbol'],
    raw_data=ibkr_trade
)
```

**IBKR Dividend Data:**
```python
ibkr_dividend = {
    'description': 'AAPL Dividend',
    'date': '2024-01-15',
    'amount': 50.00,
    'currency': 'USD'
}

entry = service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="DIVIDEND",
    amount=Decimal(str(ibkr_dividend['amount'])),
    date=datetime.strptime(ibkr_dividend['date'], '%Y-%m-%d'),
    raw_data=ibkr_dividend
)
```

## Validation and Error Handling

The service provides comprehensive validation:

- **Portfolio Existence**: Validates portfolio exists before operations
- **Data Validation**: Ensures required fields are present
- **Currency Validation**: Validates currency codes against supported currencies
- **Numeric Validation**: Validates decimal values for amounts

### Error Handling

The service handles errors gracefully:

- Returns `None` for failed activity entry creation
- Provides detailed error logging for debugging
- Validates input parameters before processing
- Handles missing or invalid data gracefully

## Usage Examples

### Basic Activity Management

```python
# Create activity management service
activity_service = ActivityManagementService(
    portfolio_repo, equity_repo, activity_entry_repo
)

# Add trade activity
trade_entry = activity_service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="TRADE",
    amount=Decimal('1500.00'),
    date=datetime(2024, 1, 15, 10, 30),
    stock_symbol="AAPL",
    raw_data={
        'symbol': 'AAPL',
        'quantity': 15,
        'price': 100.00,
        'commission': 5.00
    }
)

# Add dividend activity
dividend_entry = activity_service.add_activity_entry(
    portfolio_id=portfolio.id,
    activity_type="DIVIDEND",
    amount=Decimal('75.00'),
    date=datetime(2024, 2, 1),
    raw_data={
        'description': 'AAPL Quarterly Dividend',
        'currency': 'USD',
        'payment_date': '2024-02-01'
    }
)

# Get activity history
all_activities = activity_service.get_activity_entries(portfolio.id)
trade_activities = activity_service.get_activity_entries(
    portfolio.id, 
    activity_type="TRADE"
)
```

### Batch Import Processing

```python
# Process multiple activities in transaction
trades_data = [
    {'symbol': 'AAPL', 'amount': 1000, 'date': '2024-01-01'},
    {'symbol': 'GOOGL', 'amount': 2000, 'date': '2024-01-02'},
    {'symbol': 'MSFT', 'amount': 1500, 'date': '2024-01-03'}
]

with db.transaction() as conn:
    entries = []
    for trade in trades_data:
        entry = activity_service.add_activity_entry(
            portfolio_id=portfolio.id,
            activity_type="TRADE",
            amount=Decimal(str(trade['amount'])),
            date=datetime.fromisoformat(trade['date']),
            stock_symbol=trade['symbol'],
            conn=conn
        )
        if entry:
            entries.append(entry)
```

## Testing

The service is thoroughly tested with comprehensive unit tests covering:
- Activity entry creation for different types
- Currency parsing from various sources
- Error conditions and edge cases
- Transaction support
- Automatic equity creation
- Pagination and filtering
- Validation logic

## Integration

This service is used by:
- `PortfolioService` for backward compatibility methods
- `IBKRImportService` for trades and dividends import
- Direct integration for specialized activity operations

## Activity Types

The service supports various activity types:

- **TRADE**: Stock purchase/sale transactions
- **DIVIDEND**: Dividend payments
- **SPLIT**: Stock splits
- **MERGER**: Merger activities
- **SPINOFF**: Spinoff transactions
- **INTEREST**: Interest payments
- **FEE**: Fees and charges
- **DEPOSIT**: Cash deposits
- **WITHDRAWAL**: Cash withdrawals

## Related Documentation

- [Portfolio Service](./portfolio_service.md)
- [Holdings Management Service](./holdings_management_service.md)
- [IBKR Import Service](./ibkr_import_service.md)
- [Portfolio Domain Models](./portfolio_models.md)
