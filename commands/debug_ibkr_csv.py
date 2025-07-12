"""
Debug IBKR CSV parsing to see what data would be imported
"""
from core.csv.ibkr import IbkrCsvParser
from core.di_container import Container


def debug_ibkr_csv():
    """Debug the IBKR CSV file to see what data would be imported."""
    container = Container()
    logger = container.logger()
    
    csv_file = "/Users/stevenmyers/dev/portfolio_tracker/ibkr_year_to_date.csv"
    
    # Parse the CSV file
    parser = IbkrCsvParser(logger=logger)
    parser.parse(csv_file)
    
    print(f"\n=== IBKR CSV Debug Report ===")
    print(f"File: {csv_file}")
    print(f"Trades: {len(parser.trades)}")
    print(f"Dividends: {len(parser.dividends)}")
    print(f"Positions: {len(parser.positions)}")
    
    print(f"\n=== Trades ===")
    for i, trade in enumerate(parser.trades[:3]):  # Show first 3
        print(f"Trade {i+1}:")
        print(f"  Symbol: {trade.get('symbol')}")
        print(f"  DateTime: {trade.get('datetime')}")
        print(f"  Quantity: {trade.get('quantity')}")
        print(f"  Proceeds: {trade.get('proceeds')}")
        print()
    
    print(f"\n=== Dividends ===")
    for i, dividend in enumerate(parser.dividends[:3]):  # Show first 3
        print(f"Dividend {i+1}:")
        print(f"  Date: {dividend.get('date')}")
        print(f"  Description: {dividend.get('description')}")
        print(f"  Amount: {dividend.get('amount')}")
        print()
    
    print(f"\n=== Positions ===")
    for i, position in enumerate(parser.positions[:3]):  # Show first 3
        print(f"Position {i+1}:")
        print(f"  Symbol: {position.get('symbol')}")
        print(f"  Quantity: {position.get('quantity')}")
        print(f"  Cost Basis: {position.get('cost_basis')}")
        print()


if __name__ == "__main__":
    debug_ibkr_csv()
