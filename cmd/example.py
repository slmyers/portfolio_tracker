from core.stock_api.stock_api import fetch_stock_price

def main():
    symbols = ['DDOG', 'S']
    for symbol in symbols:
        try:
            price = fetch_stock_price(symbol)
            print(f"{symbol}: ${price:.2f}")
        except Exception as e:
            print(f"Failed to fetch price for {symbol}: {e}")

if __name__ == "__main__":
    main()
