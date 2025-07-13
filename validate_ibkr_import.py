"""Validation script to check the correctness of the IBKR CSV import."""

import csv

def validate_cash_holdings():
    """Validate cash holdings from CSV export."""
    print("=== Cash Holdings Validation ===")
    
    expected_balances = {
        "USD": 0.0,
        "CAD": 72.611174145  # From the IBKR CSV: Current cash balance
    }
    
    with open('/Users/stevenmyers/Downloads/cash_holding.csv', 'r') as f:
        reader = csv.DictReader(f)
        actual_balances = {}
        
        for row in reader:
            currency = row['currency']
            balance = float(row['balance'])
            actual_balances[currency] = balance
            print(f"  {currency}: {balance}")
    
    # Validate
    for currency, expected in expected_balances.items():
        actual = actual_balances.get(currency, 0.0)
        if abs(actual - expected) < 0.001:  # Allow for small floating point differences
            print(f"✓ {currency} balance correct: {actual}")
        else:
            print(f"✗ {currency} balance mismatch: expected {expected}, got {actual}")

def validate_activity_entries():
    """Validate activity report entries."""
    print("\n=== Activity Report Entries Validation ===")
    
    with open('/Users/stevenmyers/Downloads/activity_report_entry.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        trades_count = 0
        dividends_count = 0
        
        for row in reader:
            activity_type = row['activity_type']
            if activity_type == 'TRADE':
                trades_count += 1
            elif activity_type == 'DIVIDEND':
                dividends_count += 1
        
        print(f"  Total trades: {trades_count}")
        print(f"  Total dividends: {dividends_count}")
        
        # From the IBKR CSV, we can count expected entries
        # Let's validate some specific entries
        
def validate_specific_entries():
    """Validate specific known entries from the IBKR CSV."""
    print("\n=== Specific Entry Validation ===")
    
    with open('/Users/stevenmyers/Downloads/activity_report_entry.csv', 'r') as f:
        reader = csv.DictReader(f)
        
        # Look for the SPY trade (the big one)
        spy_trade_found = False
        expected_spy_amount = -4999.9975
        
        for row in reader:
            if row['activity_type'] == 'TRADE':
                import json
                raw_data = json.loads(row['raw_data'])
                if raw_data.get('symbol') == 'SPY':
                    actual_amount = float(row['amount'])
                    if abs(actual_amount - expected_spy_amount) < 0.001:
                        print(f"✓ SPY trade found with correct amount: {actual_amount}")
                        spy_trade_found = True
                    else:
                        print(f"✗ SPY trade amount mismatch: expected {expected_spy_amount}, got {actual_amount}")
                    break
        
        if not spy_trade_found:
            print("✗ SPY trade not found")

if __name__ == "__main__":
    validate_cash_holdings()
    validate_activity_entries()
    validate_specific_entries()
