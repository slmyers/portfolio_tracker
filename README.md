## TODO

- Implement the generic CSV parsing module (`core/csv`)
- Implement the Interactive Brokers (IBKR) CSV export module (`core/ibkr_csv`)
# Portfolio Tracker

This project is a modular Python application for tracking stock portfolios and fetching real-time stock prices using the Alpha Vantage API. It uses dependency injection for clean architecture and easy extensibility.

## Setup

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
3. Create a `.env` file in the project root with:
   ```
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

## Usage

Run the example script from the project root:
```sh
python -m cmd.example
```


## Testing

This project uses [pytest](https://docs.pytest.org/) for testing. To run all tests:

```sh
pytest
```

Unit tests for the lock module are in `tests/`.

## Project Structure

- `core/`
  - `config/`
    - `config.py`: Centralized config access and validation
    - `load_env.py`: Loads environment variables from `.env`
  - `integrations/`
    - `stock_api.py`: Fetches stock prices from Alpha Vantage
  - `di_container.py`: Dependency injection container
- `commands/`
  - `example.py`: Entry point, retrieves dependencies from the DI container
- `requirements.txt`: Python dependencies
- `.env`: Your API key (not tracked in git)

## Features
- Modular, testable architecture
- Dependency injection with [`dependency-injector`](https://python-dependency-injector.ets-labs.org/)
- Easily extendable for new integrations or commands

---
See `docs/module_architecture.md` for a detailed architecture diagram and explanation.
