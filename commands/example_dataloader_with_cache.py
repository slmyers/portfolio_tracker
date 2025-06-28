"""
Example: Using DataLoader with MemoryCache backend via DI container
"""
from core.di_container import Container
from core.dataloader import DataLoader



# Get dependencies from the DI container

container = Container()
cache_backend = container.cache()
stock_api = container.integrations().stock_api()
get_named_lock = stock_api.get_named_lock
logger = container.logger()

# Example batch load function (fetches stock prices for a list of symbols)
def batch_fetch_stock_prices(symbols):
    return [stock_api.fetch_stock_price(symbol) for symbol in symbols]


# Create DataLoader with MemoryCache backend, lock provider, and logger
loader = DataLoader(batch_load_fn=batch_fetch_stock_prices, backend=cache_backend, get_named_lock=get_named_lock, logger=logger)

# Example usage
symbols = ["AAPL", "GOOG", "MSFT"]
results = loader.load_many(symbols)
print(f"Stock prices: {dict(zip(symbols, results))}")
