import os
from core.di_container import Container
from core.csv.ibkr import IbkrCsvParser

IBKR_CSV_PATH = os.path.join(os.path.dirname(__file__), '../ibkr_year_to_date.csv')



def parse_ibkr_positions(csv_path, logger):
    """Parses the IBKR CSV and returns the positions section as a list of dicts."""
    parser = IbkrCsvParser(strict=False, logger=logger)
    parser.parse(csv_path)
    return parser.positions



def main():
    # Set up DI container
    container = Container()
    llm_agent = container.integrations().llm_agent()
    logger = container.logger()

    # Parse IBKR positions
    positions = parse_ibkr_positions(IBKR_CSV_PATH, logger)

    # Format positions for LLM
    if not positions:
        print("No positions found in the IBKR CSV.")
        return
    positions_str = "\n".join(str(position) for position in positions)

    # Compose prompt with positions data
    prompt = f"""
Below are my Interactive Brokers positions from my portfolio activity report. Please summarize my positions and provide feedback.

Positions:
{positions_str}
"""

    # Send to LLM agent
    response = llm_agent.generate_text(prompt)
    print("LLM Response:\n", response)

if __name__ == "__main__":
    main()
