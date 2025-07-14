# Refactor Plan: Portfolio Service

## Objective
Refactor the `PortfolioService` to simplify its interface and focus on ingesting activity reports. All portfolio holdings modifications will be handled internally, and unnecessary methods will be removed. The service will delegate operations to specialized services internally.

---

## Refactoring Steps

### 1. Simplify PortfolioService Interface
- **Expose only the `import_from_ibkr` method**:
  - This method will serve as the single entry point for modifying portfolio holdings.
  - All other operations will be handled internally.

### 2. Remove Unnecessary Methods
- Remove the following methods from `PortfolioService`:
  - `update_cash_balance`
  - `remove_equity_holding`

### 3. Delegate Internally to Specialized Services
- Use specialized services internally for operations like adding/removing holdings or updating balances:
  - **HoldingsManagementService**: Handles equity and cash holdings.
  - **ActivityManagementService**: Manages activity entries.
  - **IBKRImportService**: Coordinates the ingestion of activity reports and updates portfolio holdings.

### 4. Update Documentation
- Refactor the `docs/domain/portfolio_service.md` file:
  - Remove references to removed methods (`update_cash_balance`, `remove_equity_holding`).
  - Update the description of `PortfolioService` to reflect its simplified interface.
  - Add details about the delegation to specialized services.

### 5. Update Tests
- Refactor existing tests to align with the new structure:
  - Remove tests for `update_cash_balance` and `remove_equity_holding`.
  - Add tests for `import_from_ibkr` to ensure it correctly delegates operations to specialized services.
  - Add unit tests for `HoldingsManagementService`, `ActivityManagementService`, and `IBKRImportService`.

---

## Implementation Details

### PortfolioService
- **Before**:
  - Wide interface with multiple methods for portfolio management, holdings management, and activity management.
- **After**:
  - Narrow interface exposing only the `import_from_ibkr` method.
  - Delegates operations internally to specialized services.

### Specialized Services
- **HoldingsManagementService**:
  - Handles equity and cash holdings operations.
- **ActivityManagementService**:
  - Manages activity entries.
- **IBKRImportService**:
  - Coordinates the ingestion of activity reports and updates portfolio holdings.

---

## Documentation Changes

### Update `docs/domain/portfolio_service.md`
- Remove references to removed methods (`update_cash_balance`, `remove_equity_holding`).
- Update the description of `PortfolioService` to reflect its simplified interface.
- Add details about the delegation to specialized services.

### Create New Documentation
- Add new markdown files for specialized services:
  - `docs/domain/holdings_management_service.md`
  - `docs/domain/activity_management_service.md`
  - `docs/domain/ibkr_import_service.md`

---

## Testing Plan

### Update Existing Tests
- Remove tests for `update_cash_balance` and `remove_equity_holding`.
- Refactor tests for `PortfolioService` to focus on `import_from_ibkr`.

### Add New Tests
- Add unit tests for:
  - `HoldingsManagementService`
  - `ActivityManagementService`
  - `IBKRImportService`
- Ensure comprehensive coverage for:
  - Delegation logic in `PortfolioService`.
  - Internal operations in specialized services.

---

## Expected Benefits

### Simplified Interface
- The `PortfolioService` will have a single entry point for modifying portfolio holdings.

### Encapsulation
- Internal operations will be delegated to specialized services, ensuring separation of concerns.

### Alignment with Activity Reports
- Portfolio modifications will be driven entirely by activity report ingestion.

### Improved Maintainability
- Smaller, focused services will make the codebase easier to understand and extend.

### Alignment with DDD
- The portfolio is an aggregate root

---

*Last updated: 2025-07-13*
