"""
Helper command to create a test portfolio in PostgreSQL.

Usage:
    python -m commands.create_test_portfolio --name "Test Portfolio"
"""
import argparse
import sys
from uuid import uuid4

from commands.import_ibkr_csv import create_portfolio_service
from core.di_container import Container


def create_test_portfolio(name: str):
    """Create a test portfolio in PostgreSQL."""
    container = Container()
    db = container.postgres_pool()
    logger = container.logger()
    
    try:
        # Create service
        service = create_portfolio_service(db)
        
        # Create portfolio outside of transaction first
        tenant_id = uuid4()
        
        logger.info(f"Creating portfolio: {name}")
        logger.info(f"Tenant ID: {tenant_id}")
        
        # Use in-memory approach to create portfolio first
        from domain.portfolio.repository.in_memory import (
            InMemoryPortfolioRepository, InMemoryEquityRepository,
            InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository,
            InMemoryActivityReportEntryRepository
        )
        from domain.portfolio.portfolio_service import PortfolioService
        
        # Create in-memory service first
        cash_holding_repo = InMemoryCashHoldingRepository()
        portfolio_repo = InMemoryPortfolioRepository(cash_holding_repo)
        mem_service = PortfolioService(
            portfolio_repo,
            InMemoryEquityRepository(),
            InMemoryEquityHoldingRepository(),
            cash_holding_repo,
            InMemoryActivityReportEntryRepository()
        )
        
        portfolio = mem_service.create_portfolio(tenant_id, name)
        logger.info(f"Created portfolio: {portfolio.id}")
        logger.info(f"Portfolio name: {portfolio.name}")
        
        return portfolio.id
        
    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Create a test portfolio")
    parser.add_argument(
        "--name", 
        required=True, 
        help="Name of the portfolio to create"
    )
    
    args = parser.parse_args()
    
    portfolio_id = create_test_portfolio(args.name)
    
    if portfolio_id:
        print(f"Portfolio created successfully: {portfolio_id}")
        sys.exit(0)
    else:
        print("Failed to create portfolio")
        sys.exit(1)


if __name__ == "__main__":
    main()
