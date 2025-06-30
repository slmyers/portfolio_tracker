import os
from core.csv.ibkr import IbkrCsvParser

TEST_CSV_PATH = os.path.join(os.path.dirname(__file__), "../ibkr_year_to_date.csv")

def test_ibkr_parser_trades_dividends_positions():
    parser = IbkrCsvParser(strict=False)
    parser.parse(TEST_CSV_PATH)
    parser.pretty_print()
    # Trades
    trades = parser.trades
    print("TRADES:", trades)
    assert isinstance(trades, list)
    # Should find at least one trade (SPY or USD.CAD)
    print("Trade symbols:", [t.get("symbol") for t in trades])
    assert any(t.get("symbol") == "SPY" for t in trades) or any(t.get("symbol") == "USD.CAD" for t in trades)
    # Dividends
    dividends = parser.dividends
    print("DIVIDENDS:", dividends)
    assert isinstance(dividends, list)
    print("Dividend descriptions:", [d.get("description") for d in dividends])
    assert any(d.get("description") and "Dividend" in d.get("description") for d in dividends)
    # Positions
    positions = parser.positions
    print("POSITIONS:", positions)
    assert isinstance(positions, list)
    print("Position symbols:", [p.get("symbol") for p in positions])
    assert any(p.get("symbol") == "BAM" for p in positions)

def test_ibkr_pretty_print(capsys):
    parser = IbkrCsvParser(strict=False)
    parser.parse(TEST_CSV_PATH)
    parser.pretty_print()
    out = capsys.readouterr().out
    assert "Trades" in out
    assert "Dividends" in out
    assert "Open Positions" in out
