from core.di_container import Container

def main():
    container = Container()
    symbols = ['DDOG', 'S']
    for symbol in symbols:
        try:
            price = container.fetch_stock_price(symbol)
            print(f"{symbol}: ${price:.2f}")
        except Exception as e:
            print(f"Failed to fetch price for {symbol}: {e}")

if __name__ == "__main__":
    main()
