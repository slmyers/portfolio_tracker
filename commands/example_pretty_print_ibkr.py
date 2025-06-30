import os
from core.csv.ibkr import IbkrCsvParser

if __name__ == "__main__":
    # Path to the test IBKR CSV file
    test_csv_path = os.path.join(os.path.dirname(__file__), "../ibkr_year_to_date.csv")
    parser = IbkrCsvParser(strict=False)
    parser.parse(test_csv_path)
    parser.pretty_print()
