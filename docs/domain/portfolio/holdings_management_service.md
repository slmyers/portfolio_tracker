# Holdings Management Service

The `HoldingsManagementService` is a specialized service that handles all equity and cash holdings operations within portfolios. It was created as part of the PortfolioService refactor to provide focused, testable functionality for holdings management.

## Overview

This service provides a clean interface for managing both equity holdings (stocks) and cash holdings (currency balances) within portfolios. It handles the complexity of entity creation, validation, and relationship management while maintaining transaction support.

## Architecture

The service acts as a bridge between the application layer and domain repositories, coordinating operations across:
- Portfolio validation
- Equity creation and management
- Holdings creation and updates
- Cash balance management

## Dependencies

The service requires the following repository dependencies:
- `PortfolioRepository` - Portfolio validation and management
- `EquityRepository` - Equity/stock entity management
- `EquityHoldingRepository` - Equity holdings persistence
- `CashHoldingRepository` - Cash holdings persistence

## Core Methods

### Equity Holdings Management

#### `add_equity_holding(portfolio_id, symbol, quantity, cost_basis, exchange="NASDAQ", conn=None)`

Creates a new equity holding in the specified portfolio.

**Features:**
- Automatic equity creation if the symbol doesn't exist
- Portfolio validation
- Duplicate holding prevention
- Transaction support

**Parameters:**
- `portfolio_id` (UUID): Target portfolio
- `symbol` (str): Stock symbol (e.g., "AAPL")
- `quantity` (Decimal): Number of shares
- `cost_basis` (Decimal): Total cost basis
- `exchange` (str): Exchange name (default: "NASDAQ")
- `conn` (optional): Database connection for transactions

**Returns:** EquityHolding object or None if failed

**Example:**
```python
holding = service.add_equity_holding(
    portfolio_id=portfolio.id,
    symbol="AAPL",
    quantity=Decimal('100'),
    cost_basis=Decimal('15000.00'),
    exchange="NASDAQ"
)
```

#### `update_equity_holding(holding_id, quantity=None, cost_basis=None, current_value=None, conn=None)`

Updates an existing equity holding with new values.

**Parameters:**
- `holding_id` (UUID): Holding identifier
- `quantity` (Decimal, optional): New quantity
- `cost_basis` (Decimal, optional): New cost basis
- `current_value` (Decimal, optional): Current market value
- `conn` (optional): Database connection for transactions

**Returns:** Boolean success indicator

#### `get_equity_holdings(portfolio_id, conn=None)`

Retrieves all equity holdings for a portfolio.

**Parameters:**
- `portfolio_id` (UUID): Portfolio identifier
- `conn` (optional): Database connection

**Returns:** List of EquityHolding objects

### Cash Holdings Management

#### `update_cash_balance(portfolio_id, new_balance_or_currency, reason_or_new_balance=None, reason="manual", conn=None)`

Updates or creates cash holdings for a portfolio. Supports two calling patterns:

**Pattern 1: Update existing currency balance**
```python
service.update_cash_balance(
    portfolio_id=portfolio.id,
    new_balance_or_currency=Decimal('5000.00'),  # New balance
    reason_or_new_balance="DIVIDEND_PAYMENT"     # Reason
)
```

**Pattern 2: Set balance for specific currency**
```python
service.update_cash_balance(
    portfolio_id=portfolio.id,
    new_balance_or_currency=Currency.USD,        # Currency
    reason_or_new_balance=Decimal('1000.00'),    # New balance
    reason="FOREX_IMPORT"                        # Reason
)
```

**Parameters:**
- `portfolio_id` (UUID): Target portfolio
- `new_balance_or_currency` (Decimal|Currency): New balance or target currency
- `reason_or_new_balance` (str|Decimal): Reason string or new balance amount
- `reason` (str): Reason for the change (default: "manual")
- `conn` (optional): Database connection for transactions

**Returns:** Boolean success indicator

#### `get_cash_holdings(portfolio_id, conn=None)`

Retrieves all cash holdings for a portfolio.

**Parameters:**
- `portfolio_id` (UUID): Portfolio identifier
- `conn` (optional): Database connection

**Returns:** List of CashHolding objects

## Features

### Automatic Entity Creation

The service automatically creates missing entities:

**Equity Creation:**
```python
# If "TSLA" doesn't exist, it will be created automatically
holding = service.add_equity_holding(
    portfolio_id=portfolio.id,
    symbol="TSLA",  # New symbol
    quantity=Decimal('50'),
    cost_basis=Decimal('10000.00')
)
```

**Cash Holding Creation:**
```python
# Creates USD cash holding if it doesn't exist
service.update_cash_balance(
    portfolio_id=portfolio.id,
    new_balance_or_currency=Currency.USD,
    reason_or_new_balance=Decimal('1000.00')
)
```

### Transaction Support

All methods support database transactions:

```python
with db.transaction() as conn:
    # Multiple operations in single transaction
    holding1 = service.add_equity_holding(portfolio.id, "AAPL", Decimal('100'), Decimal('15000'), conn=conn)
    holding2 = service.add_equity_holding(portfolio.id, "GOOGL", Decimal('50'), Decimal('75000'), conn=conn)
    service.update_cash_balance(portfolio.id, Decimal('5000'), "INITIAL_DEPOSIT", conn=conn)
```

### Validation and Error Handling

The service provides comprehensive validation:

- **Portfolio Existence**: Validates portfolio exists before operations
- **Duplicate Prevention**: Prevents duplicate equity holdings for same symbol
- **Currency Validation**: Ensures valid currency types for cash holdings
- **Numeric Validation**: Validates decimal values for quantities and amounts

## Error Handling

The service handles errors gracefully:

- Returns `None` for failed equity holding creation
- Returns `False` for failed updates
- Validates input parameters before processing
- Provides detailed error logging for debugging

## Usage Examples

### Managing Equity Holdings

```python
# Create holdings management service
holdings_service = HoldingsManagementService(
    portfolio_repo, equity_repo, equity_holding_repo, cash_holding_repo
)

# Add new equity holding
holding = holdings_service.add_equity_holding(
    portfolio_id=portfolio.id,
    symbol="AAPL",
    quantity=Decimal('100'),
    cost_basis=Decimal('15000.00'),
    exchange="NASDAQ"
)

# Update existing holding
success = holdings_service.update_equity_holding(
    holding_id=holding.id,
    quantity=Decimal('150'),  # Increase quantity
    cost_basis=Decimal('22500.00')  # Update cost basis
)

# Get all equity holdings
holdings = holdings_service.get_equity_holdings(portfolio.id)
```

### Managing Cash Holdings

```python
# Set initial CAD balance
holdings_service.update_cash_balance(
    portfolio_id=portfolio.id,
    new_balance_or_currency=Decimal('10000.00'),
    reason_or_new_balance="INITIAL_DEPOSIT"
)

# Add USD balance
holdings_service.update_cash_balance(
    portfolio_id=portfolio.id,
    new_balance_or_currency=Currency.USD,
    reason_or_new_balance=Decimal('5000.00'),
    reason="CURRENCY_EXCHANGE"
)

# Get all cash holdings
cash_holdings = holdings_service.get_cash_holdings(portfolio.id)
```

## Testing

The service is thoroughly tested with comprehensive unit tests covering:
- Equity holding creation and updates
- Cash balance management for multiple currencies
- Error conditions and edge cases
- Transaction support
- Automatic entity creation
- Validation logic

## Integration

This service is used by:
- `PortfolioService` for backward compatibility methods
- `IBKRImportService` for positions and forex balance import
- Direct integration for specialized holdings operations

## Related Documentation

- [Portfolio Service](./portfolio_service.md)
- [Activity Management Service](./activity_management_service.md)
- [IBKR Import Service](./ibkr_import_service.md)
- [Portfolio Domain Models](./portfolio_models.md)
