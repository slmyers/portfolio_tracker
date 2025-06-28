# Cache module

- `base.py`: Defines the `CacheBackend` abstract base class for all cache backends.
- `memory.py`: Implements the in-memory cache backend (`MemoryCache`).
- `__init__.py`: Exposes the main cache classes for import.

## How to extend

To add a new backend (e.g., Redis, SQLite):
1. Create a new file (e.g., `redis.py`) in this folder.
2. Subclass `CacheBackend` and implement the required methods.
3. Add your new backend to `__init__.py` for easy import.

## Example usage

```python
from core.cache import MemoryCache

cache = MemoryCache()
cache.set("foo", 123, ttl=60)
value = cache.get("foo")  # 123
```
