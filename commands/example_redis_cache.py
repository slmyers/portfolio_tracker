
from core.dataloader import DataLoader
from core.cache.redis import RedisCache
from core.lock.in_process import InProcessLock
from core.logger import Logger
import time

logger = Logger()
cache = RedisCache(logger=logger)

# Test connection before proceeding
if not cache.test_connection():
    logger.error("Cannot connect to Redis. Exiting.")
    exit(1)

def get_named_lock(name):
    return InProcessLock(name)

def batch_fetch(keys):
    logger.info(f"Batch fetching for keys: {keys}")
    time.sleep(1)
    return [f"data_for_{k}" for k in keys]

loader = DataLoader(
    batch_load_fn=batch_fetch,
    backend=cache,
    get_named_lock=get_named_lock,
    lock_name="example_loader",
    logger=logger,
)

if __name__ == "__main__":
    # First request (should be a miss for both)
    print(loader.load_many(["AAPL", "GOOG"]))
    # Second request (should be a hit for AAPL, miss for MSFT)
    print(loader.load_many(["AAPL", "MSFT"]))
    # Wait for cache to expire
    time.sleep(11)
    # Should be a miss again
    print(loader.load_many(["AAPL"]))
