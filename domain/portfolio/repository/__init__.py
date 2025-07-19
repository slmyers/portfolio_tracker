# Portfolio repository module

from .base import (
    PortfolioRepository,
    EquityRepository,
    EquityHoldingRepository,
    CashHoldingRepository,
    ActivityReportEntryRepository,
    HoldingRepository,
)

from .in_memory import (
    InMemoryPortfolioRepository,
    InMemoryEquityRepository,
    InMemoryEquityHoldingRepository,
    InMemoryCashHoldingRepository,
    InMemoryActivityReportEntryRepository,
)

from .postgres_portfolio import PostgresPortfolioRepository
from .postgres_holdings import PostgresHoldingRepository
from .postgres_equity_holdings import PostgresEquityHoldingRepository
from .postgres_cash_holdings import PostgresCashHoldingRepository
from .postgres_equity import PostgresEquityRepository
from .postgres_activity_report_entry import PostgresActivityReportEntryRepository

__all__ = [
    # Interfaces
    'PortfolioRepository',
    'EquityRepository',
    'EquityHoldingRepository',
    'CashHoldingRepository',
    'ActivityReportEntryRepository',
    'HoldingRepository',
    
    # In-memory implementations
    'InMemoryPortfolioRepository',
    'InMemoryEquityRepository',
    'InMemoryEquityHoldingRepository',
    'InMemoryCashHoldingRepository',
    'InMemoryActivityReportEntryRepository',
    
    # PostgreSQL implementations
    'PostgresPortfolioRepository',
    'PostgresHoldingRepository',
    'PostgresEquityHoldingRepository',
    'PostgresCashHoldingRepository',
    'PostgresActivityReportEntryRepository',
    'PostgresEquityRepository',
]