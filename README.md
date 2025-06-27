# Portfolio Tracker

This is a simple Python script to fetch real-time stock prices for stocks like DDOG and S using the Alpha Vantage API.

## Setup

1. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
2. Get a free API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key).
3. Set your API key as an environment variable:
   ```sh
   export ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

## Usage

Run the script:
```sh
python main.py
```

## Files
- `main.py`: Entry point, fetches and prints stock prices.
- `stock_api/alpha_vantage.py`: Module for fetching stock prices from Alpha Vantage.
- `requirements.txt`: Python dependencies.
