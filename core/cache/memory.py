import time
from typing import Any, Optional, Dict, Tuple
from .base import CacheBackend

class MemoryCache(CacheBackend):
    """
    In-memory cache backend with optional TTL support.
    Not safe for multi-process or distributed use.
    """
    def __init__(self):
        self._store: Dict[Any, Tuple[Any, Optional[float]]] = {}

    def get(self, key: Any) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at < time.time():
            self.delete(key)
            return None
        return value

    def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        expires_at = time.time() + ttl if ttl is not None else None
        self._store[key] = (value, expires_at)

    def delete(self, key: Any) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
