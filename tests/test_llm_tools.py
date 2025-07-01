from core.integrations.llm.llm_tools import summarize_positions_tool

def test_summarize_positions_tool_formats_list():
    positions = [
        {"symbol": "AAPL", "qty": 10},
        {"symbol": "GOOG", "qty": 5}
    ]
    result = summarize_positions_tool(positions)
    assert "AAPL" in result
    assert "GOOG" in result
    assert result.count("symbol") == 2  # Each dict stringified
