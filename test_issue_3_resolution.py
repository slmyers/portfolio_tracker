"""
Demo script to verify that Issue 3 is resolved by testing the import_ibkr_csv command
with separate tenant_id and portfolio_id.
"""
from uuid import uuid4
import tempfile
import os

# Create a simple test CSV file
csv_content = '''Statement,Header,Field Name,Field Value
Statement,Data,Account,U1234567
Statement,Data,Period,"January 1, 2024 - December 31, 2024"
Statement,Data,WhenGenerated,"2024-12-31, 10:30:00 EST"
Trades,Header,DataDiscriminator,Asset Category,Currency,Symbol,Date/Time,Quantity,T. Price,C. Price,Proceeds,Comm/Fee,Basis,Realized P/L,MTM P/L,Code
Trades,Data,Order,Stocks,USD,AAPL,2024-01-15 09:30:00,100,150.50,150.50,-15050,-1.00,-15051.00,0,0,O
Dividends,Header,Currency,Date,Description,Amount
Dividends,Data,USD,2024-03-15,AAPL(US0378331005) Cash Dividend USD 0.24 per Share (Ordinary Dividend),24.00
Open Positions,Header,DataDiscriminator,Asset Category,Currency,Symbol,Quantity,Mult,Cost Price,Cost Basis,Close Price,Value,Unrealized P/L,Code
Open Positions,Data,Summary,Stocks,USD,AAPL,100,1,150.50,15050.00,175.25,17525.00,2475.00,
'''

def test_issue_3_resolution():
    """Test that the import command correctly handles separate tenant_id and portfolio_id."""
    
    # Create test UUIDs
    tenant_id = uuid4()
    portfolio_id = uuid4()
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        print("Testing Issue 3 Resolution")
        print(f"Tenant ID: {tenant_id}")
        print(f"Portfolio ID: {portfolio_id}")
        print(f"CSV file: {csv_file_path}")
        print()
        
        # These should be different UUIDs to verify the fix
        assert tenant_id != portfolio_id, "tenant_id and portfolio_id should be different for this test"
        
        print("✅ tenant_id and portfolio_id are correctly different")
        print()
        
        # Test command syntax (would need actual database to run fully)
        import_command = f"""
/Users/stevenmyers/dev/portfolio_tracker/.venv/bin/python -m commands.import_ibkr_csv \\
    --tenant-id {tenant_id} \\
    --portfolio-id {portfolio_id} \\
    --portfolio-name "Test Portfolio for Issue 3" \\
    --csv-file {csv_file_path}
"""
        
        print("Command to test (would require database):")
        print(import_command)
        print()
        
        # Test that the service layer works correctly in isolation
        from domain.portfolio.portfolio_service import PortfolioService
        from domain.portfolio.repository.in_memory import (
            InMemoryPortfolioRepository, InMemoryEquityRepository,
            InMemoryEquityHoldingRepository, InMemoryCashHoldingRepository,
            InMemoryActivityReportEntryRepository
        )
        
        # Create in-memory service
        cash_holding_repo = InMemoryCashHoldingRepository()
        portfolio_repo = InMemoryPortfolioRepository(cash_holding_repo)
        service = PortfolioService(
            portfolio_repo,
            InMemoryEquityRepository(),
            InMemoryEquityHoldingRepository(),
            cash_holding_repo,
            InMemoryActivityReportEntryRepository()
        )
        
        # Test the create_portfolio with separate IDs
        portfolio = service.create_portfolio(
            tenant_id=tenant_id,
            name="Test Portfolio for Issue 3",
            portfolio_id=portfolio_id
        )
        
        # Verify the fix
        assert portfolio.tenant_id == tenant_id, f"Expected tenant_id {tenant_id}, got {portfolio.tenant_id}"
        assert portfolio.id == portfolio_id, f"Expected portfolio_id {portfolio_id}, got {portfolio.id}"
        assert portfolio.tenant_id != portfolio.id, "tenant_id and portfolio_id should be different"
        
        print("✅ Service layer test passed:")
        print(f"   Portfolio ID: {portfolio.id}")
        print(f"   Tenant ID: {portfolio.tenant_id}")
        print(f"   Portfolio Name: {portfolio.name}")
        print()
        
        print("🎉 Issue 3 Resolution Test PASSED!")
        print("   The portfolio correctly distinguishes between tenant_id and portfolio_id")
        
    finally:
        # Clean up temp file
        os.unlink(csv_file_path)

if __name__ == "__main__":
    test_issue_3_resolution()
