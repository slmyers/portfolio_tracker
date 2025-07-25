
# Portfolio Tracker

A modular Python application for financial data analysis, portfolio management, and LLM-powered insights.  
Supports real-time stock data, robust CSV parsing (including Interactive Brokers reports), portfolio management with historical price tracking, and both OpenAI and Grok (X) LLM integrations.  
Built with dependency injection and Domain-Driven Design for clean architecture and easy extensibility.

---

## Features

- **Portfolio Management**: Complete portfolio tracking with equity and cash holdings
- **Historical Price Data**: TimescaleDB integration for efficient historical equity price storage and querying
- **IBKR Integration**: Full Interactive Brokers CSV import with trades, dividends, and positions
- **Domain-Driven Design**: Clean domain models with proper aggregates, repositories, and events
- **Modular Architecture**: Dependency injection with [`dependency-injector`](https://python-dependency-injector.ets-labs.org/)
- **Real-time Stock Data**: Alpha Vantage API integration with lazy loading and caching
- **Robust CSV Parsing**: Generic and IBKR-specific parsing capabilities
- **LLM-powered Analysis**: OpenAI and Grok/X integrations for financial insights
- **Multi-tenant Support**: Tenant isolation and user management
- **Easily Extendable**: Clean interfaces for new integrations, domains, or LLM providers

---

## Setup

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Set up your `.env` file in the project root:
   ```
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
   OPENAI_API_KEY=your_openai_key
   X_API_KEY=your_xai_grok_key
   ```
3. (Optional) See `docs/module_architecture.md` for a detailed architecture diagram and explanation.

---

## Usage

- Run the LLM IBKR summary example (compares OpenAI and Grok):
  ```sh
  python commands/example_llm_ibkr_summary.py
  ```
- Run other command-line tools from the `commands/` folder.

---

## Testing

This project uses [pytest](https://docs.pytest.org/) for testing. To run all tests:
```sh
pytest
```
Test data and edge cases are in `tests/test_data/`.

---

## Project Structure

- `core/`
  - `config/`: Configuration and environment loading
  - `csv/`: CSV parsing modules (generic and IBKR)
  - `integrations/`
    - `stock_api.py`: Stock price integration
    - `llm/`: LLM provider clients, agent, and tools
      - `llm_agent.py`: Provider-agnostic LLM agent (LangGraph)
      - `grok_llm.py`: Grok/X LLM client
      - `llm_tools.py`: Generic LLM tools
  - `di_container.py`: Dependency injection container
- `commands/`: Command-line entry points and scripts
- `requirements.txt`: Python dependencies
- `.env`: API keys (not tracked in git)
- `docs/`: Architecture and design documentation
- `ADR/`: Architectural Decision Records

---

## Extending

- Add new LLM providers by implementing a `.invoke(prompt)` client and registering in the DI container.
- Add new CSV formats or domains by extending the relevant modules and updating the DI container.

---

For more, see `docs/module_architecture.md` and `docs/core/llm_agent.md`.
