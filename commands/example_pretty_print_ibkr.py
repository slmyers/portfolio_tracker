import os
from core.csv.ibkr import IbkrCsvParser


import logging

class StdoutLogger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def info(self, msg, *a, **kw):
        print(msg)
    def debug(self, msg, *a, **kw):
        print(msg)
    def warning(self, msg, *a, **kw):
        print(msg)

if __name__ == "__main__":
    # Path to the test IBKR CSV file
    test_csv_path = os.path.join(os.path.dirname(__file__), "../ibkr_year_to_date.csv")
    logger = StdoutLogger("ibkr_example")
    parser = IbkrCsvParser(strict=False, logger=logger)
    parser.parse(test_csv_path)
    parser.pretty_print()
