# Changelog

## [Unreleased] - 2025-07-12

### Added
- **Job Domain Model**: Core job entity with status tracking and domain event integration for extensible job processing
- **PortfolioImportJob Domain Model**: Specialized job entity for portfolio import operations with interval tracking and source identification
- **Domain Events for Jobs**: Added `PortfolioImportJobSucceeded` and `PortfolioImportJobFailed` events for job lifecycle tracking
- **Idempotent Import Design**: Feature specification for preventing duplicate IBKR CSV imports using daterange intervals
- **HistoricalEquityPrice Domain Model**: New domain entity for tracking historical equity prices with TimescaleDB integration
- **HistoricalEquityPrice Repository**: Full repository implementation with PostgreSQL/TimescaleDB backend for efficient time-series data storage
- **Enhanced EquityHolding Integration**: Added lazy loading of historical prices via DataLoader pattern
- **Portfolio Service Enhancements**: 
  - Enhanced IBKR import functionality with comprehensive error handling
  - Improved transaction support across all operations
  - Better entity auto-creation and validation
  - Detailed ImportResult reporting with success/failure counts

### Enhanced
- **Portfolio Domain Documentation**: Updated with HistoricalEquityPrice entity and repository patterns
- **Entity Relationship Diagrams**: Updated to show historical price relationships
- **Module Architecture**: Added domain layer documentation with DDD principles
- **Repository Interface Examples**: Added HistoricalEquityPriceRepository interface

### Technical
- **TimescaleDB Integration**: Hypertable configuration for historical equity prices with time and space partitioning
- **DataLoader Pattern**: Efficient batching and caching for historical price queries
- **Lazy Loading**: On-demand historical price retrieval with caching support
- **API Integration**: Support for external price data APIs (Alpha Vantage) with persistence

### Documentation
- Created comprehensive Portfolio Service documentation (`docs/domain/portfolio_service.md`)
- Added Core Job Domain Model specification (`docs/domain/core/job_domain_model.md`)
- Added Portfolio Import Job Domain Model specification (`docs/domain/portfolio/portfolio_import_job_domain_model.md`)
- Added Idempotent Import Feature specification (`docs/domain/portfolio/activity_report_import_status_feature.md`)
- Updated module architecture with domain layer structure
- Enhanced README with new feature descriptions
- Added detailed usage examples and integration patterns

---

*For older changes, see git history*
