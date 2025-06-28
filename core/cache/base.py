from typing import Any, Optional

class CacheBackend:
    """
    Abstract base class for cache backends.
    """
    def get(self, key: Any) -> Optional[Any]:
        """Retrieve a value from the cache by key. Returns None if not found or expired."""
        raise NotImplementedError

    def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        """Store a value in the cache with an optional time-to-live (ttl) in seconds."""
        raise NotImplementedError

    def delete(self, key: Any) -> None:
        """Remove a value from the cache by key."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all entries from the cache."""
        raise NotImplementedError
