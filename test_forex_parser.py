#!/usr/bin/env python3

from core.csv.ibkr import IbkrCsvParser
import logging

# Test the forex balances parsing
def test_forex_parser():
    # Use standard logging instead of custom logger for test
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    parser = IbkrCsvParser(logger=logger)
    
    # Parse the CSV file
    parser.parse('./ibkr_year_to_date.csv')
    
    print(f"Found {len(parser.forex_balances)} forex balances:")
    for balance in parser.forex_balances:
        print(f"  Currency: {balance['currency']}, Description: {balance['description']}, Quantity: {balance['quantity']}, Value in CAD: {balance['value_in_cad']}")
    
    # Pretty print all sections
    parser.pretty_print(['forex_balances'])

if __name__ == '__main__':
    test_forex_parser()
