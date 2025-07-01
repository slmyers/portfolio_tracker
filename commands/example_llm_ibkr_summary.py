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
    llm_agent_openai = container.integrations().llm_agent()
    llm_agent_grok = container.integrations().llm_agent_grok()
    logger = container.logger()

    # Parse IBKR positions
    positions = parse_ibkr_positions(IBKR_CSV_PATH, logger)

    if not positions:
        print("No positions found in the IBKR CSV.")
        return

    # Test OpenAI LLM agent
    response_openai = llm_agent_openai.summarize_positions(positions)
    print("OpenAI LLM Response:\n", response_openai)

    # Test Grok LLM agent
    response_grok = llm_agent_grok.summarize_positions(positions)
    print("Grok LLM Response:\n", response_grok)

if __name__ == "__main__":
    main()
