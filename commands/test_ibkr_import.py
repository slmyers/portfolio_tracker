"""
Test the IBKR CSV import command
"""
from uuid import uuid4
from commands.import_ibkr_csv import import_ibkr_csv, create_portfolio_service
from core.di_container import Container


def test_import():
    """Test importing the sample IBKR CSV file."""
    container = Container()
    db = container.postgres_pool()
    logger = container.logger()
    
    # Create a test portfolio
    service = create_portfolio_service(db)
    tenant_id = uuid4()
    
    try:
        # Create portfolio
        portfolio = service.create_portfolio(tenant_id, "Test IBKR Import Portfolio")
        logger.info(f"Created test portfolio: {portfolio.id}")
        
        # Import CSV
        csv_file = "/Users/stevenmyers/dev/portfolio_tracker/ibkr_year_to_date.csv"
        success = import_ibkr_csv(portfolio.id, csv_file)
        
        if success:
            logger.info("Import test successful!")
            
            # Check what was imported
            holdings = service.get_equity_holdings(portfolio.id)
            activities = service.get_activity_entries(portfolio.id)
            
            logger.info(f"Imported {len(holdings)} holdings and {len(activities)} activity entries")
            
            return True
        else:
            logger.error("Import test failed!")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False


if __name__ == "__main__":
    test_import()
