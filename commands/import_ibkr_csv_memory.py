"""
Command to import IBKR CSV file into a portfolio using in-memory storage.

Usage:
    python -m commands.import_ibkr_csv_memory --csv-file <path>
"""
import argparse
import sys
from uuid import uuid4
from pathlib import Path

from core.csv.ibkr import IbkrCsvParser
from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.repository.in_memory import (
    InMemoryPortfolioRepository,
    InMemoryEquityRepository, 
    InMemoryEquityHoldingRepository,
    InMemoryCashHoldingRepository,
    InMemoryActivityReportEntryRepository
)
from core.di_container import Container


def create_in_memory_portfolio_service() -> PortfolioService:
    """Create a PortfolioService with in-memory repositories."""
    cash_holding_repo = InMemoryCashHoldingRepository()
    portfolio_repo = InMemoryPortfolioRepository(cash_holding_repo)
    equity_repo = InMemoryEquityRepository()
    equity_holding_repo = InMemoryEquityHoldingRepository()
    activity_entry_repo = InMemoryActivityReportEntryRepository()
    
    return PortfolioService(
        portfolio_repo,
        equity_repo,
        equity_holding_repo,
        cash_holding_repo,
        activity_entry_repo
    )


def import_ibkr_csv_memory(csv_file_path: str) -> bool:
    """
    Import IBKR CSV data into a new portfolio using in-memory storage.
    
    Args:
        csv_file_path: Path to the IBKR CSV file
        
    Returns:
        bool: True if import was successful, False otherwise
    """
    container = Container()
    logger = container.logger()
    
    # Validate inputs
    if not Path(csv_file_path).exists():
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    try:
        # Parse the CSV file
        logger.info(f"Parsing IBKR CSV file: {csv_file_path}")
        parser = IbkrCsvParser(logger=logger)
        parser.parse(csv_file_path)
        
        trades = parser.trades
        dividends = parser.dividends
        positions = parser.positions
        
        logger.info(f"Parsed {len(trades)} trades, {len(dividends)} dividends, {len(positions)} positions")
        
        if not trades and not dividends and not positions:
            logger.warning("No data found in CSV file")
            return False
        
        # Create service with in-memory repositories
        service = create_in_memory_portfolio_service()
        
        # Create a test portfolio
        tenant_id = uuid4()
        portfolio = service.create_portfolio(tenant_id, "IBKR Import Test Portfolio")
        logger.info(f"Created portfolio: {portfolio.id}")
        
        # Import data
        logger.info(f"Starting import for portfolio {portfolio.id}")
        
        result = service.import_from_ibkr(
            portfolio_id=portfolio.id,
            trades=trades,
            dividends=dividends,
            positions=positions
        )
        
        if result.success:
            logger.info(f"Successfully imported IBKR data for portfolio {portfolio.id}")
            logger.info(f"Import summary: {result.total_items_processed} items processed, "
                      f"{result.total_models_created} models created, "
                      f"{result.total_items_skipped} items skipped")
            
            # Show results
            holdings = service.get_equity_holdings(portfolio.id)
            activities = service.get_activity_entries(portfolio.id)
            
            logger.info("Import results:")
            logger.info(f"  - {len(holdings)} equity holdings")
            logger.info(f"  - {len(activities)} activity entries")
            
            # Show some holdings
            logger.info("Holdings:")
            for holding in holdings:
                equity = service.equity_repo.get(holding.equity_id)
                logger.info(f"  - {equity.symbol if equity else 'Unknown'}: {holding.quantity} shares")
            
            return True
        else:
            logger.error(f"Failed to import IBKR data for portfolio {portfolio.id}")
            logger.error(f"Error: {result.error_message} ({result.error_type})")
            if result.failed_items:
                logger.error(f"{len(result.failed_items)} items failed to import")
            return False
                    
    except Exception as e:
        logger.error(f"Error importing IBKR CSV: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Import IBKR CSV file into a new portfolio (in-memory)")
    parser.add_argument(
        "--csv-file", 
        required=True, 
        help="Path to the IBKR CSV file"
    )
    
    args = parser.parse_args()
    
    success = import_ibkr_csv_memory(args.csv_file)
    
    if success:
        print("Import completed successfully")
        sys.exit(0)
    else:
        print("Import failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
