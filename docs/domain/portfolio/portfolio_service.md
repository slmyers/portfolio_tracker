# Portfolio Service

The `PortfolioService` provides the application layer for portfolio operations, serving as the primary entry point for portfolio management. After a significant refactor, it now focuses on coordination and delegation while maintaining backward compatibility.

## Overview

The Portfolio Service has been refactored to follow Domain-Driven Design principles by:
- Providing a single entry point for portfolio operations
- Maintaining backward compatibility through delegation
- Using composition with specialized services for complex operations
- Focusing on coordination rather than implementation details

The service now delegates specialized operations to focused services while maintaining a clean interface for core portfolio operations.

## Architecture

```
PortfolioService
├── HoldingsManagementService
│   ├── add_equity_holding()
│   ├── update_cash_balance()
│   └── get_holdings()
├── ActivityManagementService
│   ├── add_activity_entry()
│   └── get_activity_entries()
└── IBKRImportService
    └── import_from_ibkr()
```

## Dependencies

The service depends on the following repositories via dependency injection:

- `PortfolioRepository`: Core portfolio management
- `EquityRepository`: Equity/stock management  
- `EquityHoldingRepository`: Equity holdings management
- `CashHoldingRepository`: Cash holdings management
- `ActivityReportEntryRepository`: Activity report entry management

Additionally, it composes with specialized services:
- `HoldingsManagementService`: Handles equity and cash holdings operations
- `ActivityManagementService`: Manages activity entries
- `IBKRImportService`: Coordinates IBKR data import and portfolio updates

## Core Operations

### Portfolio CRUD Operations

The service maintains focused responsibility for core portfolio operations:

```python
def create_portfolio(self, tenant_id: UUID, name: str, portfolio_id: Optional[UUID] = None, conn=None) -> Portfolio
def get_portfolio(self, portfolio_id: UUID, conn=None) -> Optional[Portfolio]
def get_portfolios_by_tenant(self, tenant_id: UUID, conn=None) -> List[Portfolio]
def rename_portfolio(self, portfolio_id: UUID, new_name: str, conn=None) -> bool
def delete_portfolio(self, portfolio_id: UUID, conn=None) -> bool
```

### Primary Data Import Entry Point

The main method for modifying portfolio holdings:

```python
def import_from_ibkr(self, portfolio_id: UUID, trades: List[dict], dividends: List[dict], 
                    positions: List[dict], forex_balances: List[dict], conn=None) -> ImportResult
```

This method serves as the single entry point for portfolio modifications, delegating to `IBKRImportService` for coordination between holdings and activity management.

### Backward Compatibility Methods

These methods are maintained for backward compatibility but delegate to specialized services:

#### Holdings Management (Delegated to HoldingsManagementService)

```python
def add_equity_holding(self, portfolio_id: UUID, symbol: str, quantity: Decimal, 
                      cost_basis: Decimal, exchange: str = "NASDAQ", conn=None) -> Optional[EquityHolding]
def update_cash_balance(self, portfolio_id: UUID, new_balance_or_currency, 
                       reason_or_new_balance, reason: str = "manual", conn=None) -> bool
def get_equity_holdings(self, portfolio_id: UUID, conn=None) -> List[EquityHolding]
def get_cash_holdings(self, portfolio_id: UUID, conn=None) -> List[CashHolding]
```

#### Activity Management (Delegated to ActivityManagementService)

```python
def add_activity_entry(self, portfolio_id: UUID, activity_type: str, amount: Decimal,
                      date: datetime, stock_symbol: Optional[str] = None, 
                      raw_data: Optional[dict] = None) -> Optional[ActivityReportEntry]
def get_activity_entries(self, portfolio_id: UUID, activity_type: Optional[str] = None,
                        limit: int = 100, offset: int = 0, conn=None) -> List[ActivityReportEntry]
```

## Key Architectural Changes

### 1. **Service Composition**

The refactored service uses composition to delegate specialized operations:

- **HoldingsManagementService**: Handles all equity and cash holdings operations
- **ActivityManagementService**: Manages activity report entries
- **IBKRImportService**: Coordinates comprehensive IBKR data import

### 2. **Single Entry Point for Modifications**

`import_from_ibkr()` serves as the primary method for portfolio modifications, ensuring:
- Consistent data import patterns
- Comprehensive error handling and reporting
- Coordination between holdings and activity management
- Detailed success/failure tracking

### 3. **Backward Compatibility**

Existing methods are preserved to avoid breaking changes, but internally delegate to specialized services. This allows gradual migration while maintaining existing functionality.

### 4. **Transaction Support**

All methods support transaction management through the optional `conn` parameter:

```python
# Single operation
portfolio = service.create_portfolio(tenant_id, "My Portfolio")

# Multiple operations in transaction  
with db.transaction() as conn:
    portfolio = service.create_portfolio(tenant_id, "My Portfolio", conn=conn)
    result = service.import_from_ibkr(portfolio.id, trades, dividends, positions, forex_balances, conn=conn)
```

## IBKR Import Integration

The `import_from_ibkr` method provides comprehensive import functionality through delegation to `IBKRImportService`:

- **Trades**: Imported as activity entries with automatic equity creation
- **Dividends**: Imported as activity entries with currency handling
- **Positions**: Converted to equity holdings with automatic equity creation
- **Forex Balances**: Imported as cash holdings with currency validation
- **Error Handling**: Returns detailed `ImportResult` with success/failure counts and error details

### Import Result Structure

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
    equities_created: int = 0
    
    # Failures
    skipped_trades: int = 0
    skipped_dividends: int = 0
    skipped_positions: int = 0
    failed_items: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    error_type: Optional[str] = None
```

### 4. **Domain Event Integration**

The service properly propagates domain events generated by aggregates:

- Portfolio creation, updates, deletion
- Holding additions, updates, removals  
- Activity entry additions
- Cash balance updates
- Import completion events

### 5. **Validation and Error Handling**

- **Duplicate Holdings**: Prevents adding multiple holdings for the same equity in a portfolio
- **Ownership Validation**: Ensures holdings belong to the correct portfolio
- **Entity Existence**: Validates referenced entities exist
- **Data Consistency**: Maintains referential integrity across operations

## Usage Examples

### Creating and Managing a Portfolio

```python
# Create service with DI
service = PortfolioService(
    portfolio_repo=portfolio_repo,
    equity_repo=equity_repo, 
    equity_holding_repo=equity_holding_repo,
    cash_holding_repo=cash_holding_repo,
    activity_entry_repo=activity_entry_repo
)

# Create portfolio
portfolio = service.create_portfolio(tenant_id, "My Investment Portfolio")

# Add equity holdings
apple_holding = service.add_equity_holding(
    portfolio.id, "AAPL", Decimal('100'), Decimal('15000')
)
google_holding = service.add_equity_holding(
    portfolio.id, "GOOGL", Decimal('50'), Decimal('12500')
)

# Update cash balance
service.update_cash_balance(portfolio.id, Decimal('5000'), "initial_deposit")

# Add activity entry
service.add_activity_entry(
    portfolio.id, "DIVIDEND", Decimal('150'), datetime.now(), "AAPL"
)
```

### IBKR Import Example

```python
# Parse IBKR CSV data (using existing parser)
trades, dividends, positions = parse_ibkr_csv("activity_report.csv")

# Import into portfolio
result = service.import_from_ibkr(portfolio.id, trades, dividends, positions)

if result.success:
    print(f"Successfully imported {result.trades_imported} trades, "
          f"{result.dividends_imported} dividends, {result.positions_imported} positions")
else:
    print(f"Import failed: {result.error_message}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
```

## Architecture Considerations

### 1. **Separation of Concerns**

- **Domain Logic**: Handled by domain models and aggregates
- **Coordination**: Managed by the service layer
- **Persistence**: Delegated to repositories
- **Transactions**: Managed at the service layer

### 2. **Dependency Injection**

The service depends on repository interfaces, not concrete implementations, enabling:

- Easy testing with mock repositories
- Swapping persistence implementations
- Clean separation between layers

### 3. **Transaction Boundaries** 

The service defines clear transaction boundaries:

- **Single Operations**: Auto-managed transactions
- **Multi-Operation**: Explicit transaction control via `conn` parameter
- **Import Operations**: Single transaction for consistency

### 4. **Error Handling Strategy**

- **Domain Errors**: Propagated from aggregates (e.g., `DuplicateHoldingError`)
- **Validation Errors**: Handled at service layer 
- **Import Errors**: Collected and returned in `ImportResult`
- **Transaction Rollback**: Automatic on exceptions

## Integration Points

### With Domain Layer
- Calls domain aggregate methods
- Respects domain invariants and business rules
- Propagates domain events

### With Infrastructure Layer
- Uses repository interfaces for persistence
- Manages database transactions
- Handles external service integration (IBKR import)

### With Application Layer
- Provides high-level operations for controllers/CLI
- Handles cross-cutting concerns (logging, caching)
- Manages request/response transformation

---

*Last updated: 2025-07-12*
