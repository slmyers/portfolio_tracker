import os
from core.csv.ibkr import IbkrCsvParser
import logging

TEST_CSV_PATH = os.path.join(os.path.dirname(__file__), "../ibkr_year_to_date.csv")


class ListLogger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
    def info(self, msg, *a, **kw):
        self.records.append(str(msg))
    def debug(self, msg, *a, **kw):
        self.records.append(str(msg))
    def warning(self, msg, *a, **kw):
        self.records.append(str(msg))

def test_ibkr_parser_trades_dividends_positions():
    logger = ListLogger("test_ibkr")
    parser = IbkrCsvParser(strict=False, logger=logger)
    parser.parse(TEST_CSV_PATH)
    parser.pretty_print()
    # Trades
    trades = parser.trades
    assert isinstance(trades, list)
    assert any(t.get("symbol") == "SPY" for t in trades) or any(t.get("symbol") == "USD.CAD" for t in trades)
    # Dividends
    dividends = parser.dividends
    assert isinstance(dividends, list)
    assert any(d.get("description") and "Dividend" in d.get("description") for d in dividends)
    # Positions
    positions = parser.positions
    assert isinstance(positions, list)
    assert any(p.get("symbol") == "BAM" for p in positions)

def test_ibkr_pretty_print():
    logger = ListLogger("test_ibkr_pretty")
    parser = IbkrCsvParser(strict=False, logger=logger)
    parser.parse(TEST_CSV_PATH)
    parser.pretty_print()
    out = "\n".join(logger.records)
    assert "Trades" in out
    assert "Dividends" in out
    assert "Open Positions" in out

def test_ibkr_statement_metadata():
    logger = ListLogger("test_ibkr_meta")
    parser = IbkrCsvParser(strict=False, logger=logger)
    parser.parse(TEST_CSV_PATH)
    meta = parser.meta
    from pprint import pprint
    pprint(logger.records)
    assert meta is not None, "Statement metadata should be parsed."
    assert meta.get("BrokerName") == "Interactive Brokers Canada Inc.", "BrokerName should match."
    assert "PeriodStart" in meta and "PeriodEnd" in meta, "PeriodStart and PeriodEnd should be present."
    assert meta["PeriodStart"].year == 2025, "PeriodStart year should be 2025."
