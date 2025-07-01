def summarize_positions_tool(positions: list) -> str:
    """Format or summarize positions for the LLM."""
    return "\n".join(str(position) for position in positions)
