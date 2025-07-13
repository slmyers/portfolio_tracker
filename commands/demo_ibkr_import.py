"""
Complete IBKR CSV import demo command.

This command demonstrates the full IBKR CSV import functionality:
1. Parses an IBKR CSV file
2. Creates a portfolio 
3. Imports trades, dividends, and positions
4. Shows detailed results

Usage:
    python -m commands.demo_ibkr_import --csv-file <path>
"""
import argparse
import sys
from uuid import uuid4
from pathlib import Path
from decimal import Decimal

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


def create_demo_service() -> PortfolioService:
    """Create a PortfolioService with in-memory repositories for demo."""
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


def demo_ibkr_import(csv_file_path: str) -> bool:
    """
    Complete demo of IBKR CSV import functionality.
    
    Args:
        csv_file_path: Path to the IBKR CSV file
        
    Returns:
        bool: True if demo completed successfully
    """
    container = Container()
    logger = container.logger()
    
    # Validate inputs
    if not Path(csv_file_path).exists():
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    print("🚀 Starting IBKR CSV Import Demo")
    print(f"📁 File: {csv_file_path}")
    print()
    
    try:
        # Step 1: Parse the CSV file
        print("📊 Step 1: Parsing IBKR CSV file...")
        parser = IbkrCsvParser(logger=logger)
        parser.parse(csv_file_path)
        
        trades = parser.trades
        dividends = parser.dividends
        positions = parser.positions
        
        print(f"   ✅ Parsed {len(trades)} trades")
        print(f"   ✅ Parsed {len(dividends)} dividends") 
        print(f"   ✅ Parsed {len(positions)} positions")
        print()
        
        if not trades and not dividends and not positions:
            print("❌ No data found in CSV file")
            return False
        
        # Step 2: Create portfolio service and portfolio
        print("🏦 Step 2: Creating portfolio...")
        service = create_demo_service()
        
        tenant_id = uuid4()
        portfolio = service.create_portfolio(tenant_id, "IBKR Import Demo Portfolio")
        print(f"   ✅ Created portfolio: {portfolio.id}")
        print(f"   📝 Portfolio name: {portfolio.name}")
        print(f"   💰 Initial cash balance: ${portfolio.cash_balance}")
        print()
        
        # Step 3: Import the data
        print("📥 Step 3: Importing IBKR data...")
        
        result = service.import_from_ibkr(
            portfolio_id=portfolio.id,
            trades=trades,
            dividends=dividends,
            positions=positions
        )
        
        if not result.success:
            print("❌ Import failed")
            print(f"   Error: {result.error_message} ({result.error_type})")
            if result.failed_items:
                print(f"   {len(result.failed_items)} items failed to import")
            return False
        
        print("   ✅ Import completed successfully!")
        print(f"   📊 Summary: {result.total_items_processed} items processed, "
              f"{result.total_models_created} models created")
        if result.warnings:
            print(f"   ⚠️  {len(result.warnings)} warnings")
        print()
        
        # Step 4: Show detailed results
        print("📈 Step 4: Import Results")
        print("=" * 50)
        
        # Get imported data
        holdings = service.get_equity_holdings(portfolio.id)
        activities = service.get_activity_entries(portfolio.id)
        trade_activities = [a for a in activities if a.activity_type == 'TRADE']
        dividend_activities = [a for a in activities if a.activity_type == 'DIVIDEND']
        
        print("📊 Summary:")
        print(f"   • {len(holdings)} equity holdings")
        print(f"   • {len(trade_activities)} trade activities")
        print(f"   • {len(dividend_activities)} dividend activities")
        print(f"   • {len(activities)} total activities")
        print()
        
        # Show holdings details
        print("🏪 Holdings:")
        total_cost_basis = Decimal('0')
        for holding in holdings:
            equity = service.equity_repo.get(holding.equity_id)
            symbol = equity.symbol if equity else 'Unknown'
            cost_basis = holding.cost_basis
            total_cost_basis += cost_basis
            print(f"   • {symbol:8} | {holding.quantity:>8} shares | Cost Basis: ${cost_basis:>10.2f}")
        print(f"   {'Total':9} | {'':>8} {'':>6} | Cost Basis: ${total_cost_basis:>10.2f}")
        print()
        
        # Show recent activities
        print("📅 Recent Activities (last 5):")
        recent_activities = sorted(activities, key=lambda a: a.date, reverse=True)[:5]
        for activity in recent_activities:
            equity = service.equity_repo.get(activity.equity_id) if activity.equity_id else None
            symbol = equity.symbol if equity else 'N/A'
            date_str = activity.date.strftime('%Y-%m-%d')
            print(f"   • {date_str} | {activity.activity_type:8} | {symbol:8} | ${activity.amount:>10.2f}")
        print()
        
        # Show dividend summary
        if dividend_activities:
            print("💰 Dividend Summary:")
            total_dividends = sum(d.amount for d in dividend_activities)
            print(f"   • Total dividends: ${total_dividends:.2f}")
            print(f"   • Number of payments: {len(dividend_activities)}")
            
            # Group by equity
            dividend_by_symbol = {}
            for div in dividend_activities:
                equity = service.equity_repo.get(div.equity_id) if div.equity_id else None
                symbol = equity.symbol if equity else 'Various'
                if symbol not in dividend_by_symbol:
                    dividend_by_symbol[symbol] = []
                dividend_by_symbol[symbol].append(div.amount)
            
            for symbol, amounts in dividend_by_symbol.items():
                total = sum(amounts)
                count = len(amounts)
                print(f"   • {symbol}: ${total:.2f} ({count} payments)")
            print()
        
        print("🎉 Demo completed successfully!")
        print(f"📋 Portfolio ID for reference: {portfolio.id}")
        
        return True
                    
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Demo IBKR CSV import functionality")
    parser.add_argument(
        "--csv-file", 
        required=True, 
        help="Path to the IBKR CSV file"
    )
    
    args = parser.parse_args()
    
    success = demo_ibkr_import(args.csv_file)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
