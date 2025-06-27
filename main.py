
from load_env import load_env
from stock_api.alpha_vantage import fetch_stock_price
import os

def main():
    load_env()
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if api_key:
        masked = '*' * (len(api_key) - 4) + api_key[-4:]
        print(f"[DEBUG] ALPHA_VANTAGE_API_KEY loaded: {masked}")
    else:
        print("[DEBUG] ALPHA_VANTAGE_API_KEY not found in environment variables.")

    symbols = ['DDOG', 'S']
    for symbol in symbols:
        try:
            price = fetch_stock_price(symbol)
            print(f"{symbol}: ${price:.2f}")
        except Exception as e:
            print(f"Failed to fetch price for {symbol}: {e}")

if __name__ == "__main__":
    main()
