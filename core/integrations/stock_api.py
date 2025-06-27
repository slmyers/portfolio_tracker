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
