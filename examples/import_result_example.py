#!/usr/bin/env python3
"""
Example demonstrating the new ImportResult from import_from_ibkr method.

This shows how to use the enhanced return value that provides detailed 
metadata about the import operation.
"""

from uuid import uuid4
from decimal import Decimal
from datetime import datetime
from domain.portfolio.models.import_result import ImportResult

def example_import_result_usage():
    """Example showing how to handle ImportResult from import_from_ibkr."""
    
    # Example data for import
    trades = [
        {
            'symbol': 'AAPL',
            'datetime': '2025-01-15, 10:30:00',
            'proceeds': Decimal('1500.00')
        },
        {
            'symbol': 'GOOGL', 
            'datetime': '2025-01-16, 14:20:00',
            'proceeds': Decimal('2800.00')
        }
    ]
    
    dividends = [
        {
            'description': 'AAPL Dividend',
            'date': '2025-01-20',
            'amount': Decimal('25.50')
        }
    ]
    
    positions = [
        {
            'symbol': 'AAPL',
            'quantity': '10',
            'cost_basis': '150.00'
        }
    ]
    
    # Mock service call (replace with actual service instance)
    # result = portfolio_service.import_from_ibkr(
    #     portfolio_id=some_portfolio_id,
    #     trades=trades,
    #     dividends=dividends, 
    #     positions=positions
    # )
    
    # Example of handling the result
    print("📥 IBKR Import Example")
    print("=" * 50)
    
    # Create example result for demonstration
    result = ImportResult(
        success=True,
        import_source='IBKR_CSV',
        portfolio_id=str(uuid4()),
        trades_imported=2,
        dividends_imported=1,
        positions_imported=1,
        activity_entries_created=3,
        equity_holdings_created=1,
        equities_created=1,
        started_at=datetime.now(),
        completed_at=datetime.now()
    )
    result.add_warning("Skipped 1 trade with missing symbol")
    
    # Handle successful import
    if result.success:
        print("✅ Import completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Portfolio ID: {result.portfolio_id}")
        print(f"   • Source: {result.import_source}")
        print(f"   • Duration: {result.duration_seconds:.2f} seconds")
        print()
        
        print(f"📈 Items Processed:")
        print(f"   • Trades imported: {result.trades_imported}")
        print(f"   • Dividends imported: {result.dividends_imported}")
        print(f"   • Positions imported: {result.positions_imported}")
        print(f"   • Total processed: {result.total_items_processed}")
        print()
        
        print(f"🏗️  Models Created:")
        print(f"   • Activity entries: {result.activity_entries_created}")
        print(f"   • Equity holdings: {result.equity_holdings_created}")
        print(f"   • New equities: {result.equities_created}")
        print(f"   • Total models: {result.total_models_created}")
        print()
        
        if result.warnings:
            print(f"⚠️  Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                print(f"   • {warning}")
            print()
        
        if result.total_items_skipped > 0:
            print(f"⏭️  Skipped Items:")
            print(f"   • Trades: {result.skipped_trades}")
            print(f"   • Dividends: {result.skipped_dividends}")
            print(f"   • Positions: {result.skipped_positions}")
            print(f"   • Total skipped: {result.total_items_skipped}")
            print()
            
    else:
        # Handle failed import
        print("❌ Import failed!")
        print(f"🚨 Error: {result.error_message}")
        print(f"📝 Error Type: {result.error_type}")
        print()
        
        if result.failed_items:
            print(f"💥 Failed Items ({len(result.failed_items)}):")
            for failed_item in result.failed_items[:5]:  # Show first 5
                print(f"   • {failed_item['type']}: {failed_item['error']}")
            if len(result.failed_items) > 5:
                print(f"   • ... and {len(result.failed_items) - 5} more")
            print()
        
        # You might want to log these details or store them for later analysis
        # logger.error(f"Import failed: {result.error_message}")
        # for failed_item in result.failed_items:
        #     logger.error(f"Failed {failed_item['type']}: {failed_item['error']}")

    # Example of using the result for business logic
    if result.success and result.total_models_created > 0:
        print("🔄 Next steps:")
        print("   • Refresh portfolio cache")
        print("   • Update portfolio value calculations")
        print("   • Send notification to user")
    elif not result.success:
        print("🔄 Next steps:")
        print("   • Log error details for debugging")
        print("   • Notify user of import failure")
        print("   • Review failed items for retry")

if __name__ == "__main__":
    example_import_result_usage()
