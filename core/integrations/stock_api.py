from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional
import requests
from core.config.config import get_alpha_vantage_api_key

BASE_URL = 'https://www.alphavantage.co/query'

def fetch_stock_price(symbol: str) -> float:
    """
    Fetch the latest stock price for the given symbol from Alpha Vantage API.
    """
    api_key: str = get_alpha_vantage_api_key()
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '1min',
        'apikey': api_key
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if 'Time Series (1min)' not in data:
        raise Exception(f"Error fetching data for {symbol}: {data.get('Note') or data.get('Error Message') or data}")
    latest_time = sorted(data['Time Series (1min)'].keys())[-1]
    latest_price = data['Time Series (1min)'][latest_time]['4. close']
    return float(latest_price)

def batch_fetch_stock_prices(symbols: list[str], max_workers: Optional[int] = 4) -> list[float]:
    """
    Fetch the latest stock prices for a list of symbols from Alpha Vantage API in parallel.
    Returns a list of prices in the same order as the input symbols.
    max_workers controls the number of parallel requests (default: 4).
    """
    results = [None] * len(symbols)
    def fetch_and_store(idx, symbol):
        try:
            return idx, fetch_stock_price(symbol)
        except Exception:
            return idx, None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_and_store, idx, symbol) for idx, symbol in enumerate(symbols)]
        for future in as_completed(futures):
            idx, price = future.result()
            results[idx] = price
    return results