"""
Command to import IBKR CSV file into a portfolio.

Usage:
    python -m commands.import_ibkr_csv --portfolio-id <uuid> --csv-file <path>
"""
import argparse
import sys
from uuid import UUID
from pathlib import Path

from core.di_container import Container
from core.csv.ibkr import IbkrCsvParser
from domain.portfolio.portfolio_service import PortfolioService
from domain.portfolio.repository import (
    PostgresPortfolioRepository,
    PostgresEquityRepository, 
    PostgresEquityHoldingRepository,
    PostgresCashHoldingRepository,
    PostgresActivityReportEntryRepository
)


def create_portfolio_service(db) -> PortfolioService:
    """Create a PortfolioService with PostgreSQL repositories."""
    portfolio_repo = PostgresPortfolioRepository(db)
    equity_repo = PostgresEquityRepository(db)
    equity_holding_repo = PostgresEquityHoldingRepository(db)
    cash_holding_repo = PostgresCashHoldingRepository(db)
    activity_entry_repo = PostgresActivityReportEntryRepository(db)
    
    return PortfolioService(
        portfolio_repo,
        equity_repo,
        equity_holding_repo,
        cash_holding_repo,
        activity_entry_repo
    )


def import_ibkr_csv(portfolio_id: UUID, portfolio_name: str, csv_file_path: str) -> bool:
    """
    Import IBKR CSV data into the specified portfolio.
    
    Controller-style method that:
    1. Parses the CSV file
    2. Creates the portfolio if it doesn't exist
    3. Opens a transaction
    4. Imports the data
    5. Commits the transaction
    
    Args:
        portfolio_id: UUID of the portfolio to import into
        portfolio_name: Name of the portfolio to create if it doesn't exist
        csv_file_path: Path to the IBKR CSV file
        
    Returns:
        bool: True if import was successful, False otherwise
    """
    container = Container()
    db = container.postgres_pool()
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
        
        # Create service
        service = create_portfolio_service(db)

        # Open transaction
        with db.connection() as (conn, deadline):
            try:
                # Set autocommit to False for transaction management
                conn.autocommit = False

                # Check if portfolio exists, create if not
                portfolio = service.get_portfolio(portfolio_id, conn=conn)
                if not portfolio:
                    logger.info(f"Portfolio {portfolio_id} not found. Creating new portfolio: {portfolio_name}")
                    # Use portfolio_id as tenant_id for now (this should be changed in a real multi-tenant system)
                    portfolio = service.create_portfolio(portfolio_id, portfolio_name, conn=conn)
                    logger.info(f"Created portfolio: {portfolio.id}")

                logger.info(f"Using portfolio: {portfolio.id} - {portfolio.name}")
                
                # Import data within transaction - use the actual portfolio ID
                result = service.import_from_ibkr(
                    portfolio_id=portfolio.id,  # Use the actual portfolio ID, not the input ID
                    trades=trades,
                    dividends=dividends,
                    positions=positions,
                    conn=conn
                )
                
                if result.success:
                    # Commit transaction
                    conn.commit()
                    logger.info(f"Successfully imported IBKR data for portfolio {portfolio.id}")
                    logger.info(f"Import summary: {result.total_items_processed} items processed, "
                              f"{result.total_models_created} models created, "
                              f"{result.total_items_skipped} items skipped")
                    
                    if result.warnings:
                        logger.warning(f"Import completed with {len(result.warnings)} warnings:")
                        for warning in result.warnings:
                            logger.warning(f"  - {warning}")
                    
                    # Show results (outside transaction)
                    holdings = service.get_equity_holdings(portfolio.id, conn=conn)
                    activities = service.get_activity_entries(portfolio.id, conn=conn)
                    
                    logger.info(f"Import results:")
                    logger.info(f"  - {len(holdings)} equity holdings") 
                    logger.info(f"  - {len(activities)} activity entries")
                    
                    return True
                else:
                    # Rollback on failure
                    conn.rollback()
                    logger.error(f"Failed to import IBKR data for portfolio {portfolio.id}")
                    logger.error(f"Error: {result.error_message} ({result.error_type})")
                    
                    if result.failed_items:
                        logger.error(f"{len(result.failed_items)} items failed to import:")
                        for failed_item in result.failed_items[:5]:  # Show first 5 failures
                            logger.error(f"  - {failed_item['type']}: {failed_item['error']}")
                        if len(result.failed_items) > 5:
                            logger.error(f"  ... and {len(result.failed_items) - 5} more")
                    
                    return False
                    
            except Exception as e:
                # Rollback on exception
                conn.rollback()
                logger.error(f"Error during import: {e}")
                import traceback
                traceback.print_exc()
                raise
                
    except Exception as e:
        logger.error(f"Error importing IBKR CSV: {e}")
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Import IBKR CSV file into a portfolio")
    parser.add_argument(
        "--portfolio-id", 
        required=True, 
        help="UUID of the portfolio to import into"
    )
    parser.add_argument(
        "--portfolio-name", 
        required=True, 
        help="Name of the portfolio to create if it doesn't exist"
    )
    parser.add_argument(
        "--csv-file", 
        required=True, 
        help="Path to the IBKR CSV file"
    )
    
    args = parser.parse_args()
    
    try:
        portfolio_id = UUID(args.portfolio_id)
    except ValueError:
        print(f"Error: Invalid portfolio ID: {args.portfolio_id}")
        sys.exit(1)
    
    success = import_ibkr_csv(portfolio_id, args.portfolio_name, args.csv_file)
    
    if success:
        print("Import completed successfully")
        sys.exit(0)
    else:
        print("Import failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
