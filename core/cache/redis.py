from typing import Any, Optional, Protocol
import redis
from .base import CacheBackend


class RedisClientProtocol(Protocol):
    def ping(self) -> bool: ...
    def get(self, key: Any) -> Optional[Any]: ...
    def set(self, key: Any, value: Any): ...
    def setex(self, key: Any, ttl: int, value: Any): ...
    def delete(self, key: Any): ...
    def flushdb(self): ...

class RedisClientFactory:
    @staticmethod
    def create(host: str = 'localhost', port: int = 6379, db: int = 0) -> RedisClientProtocol:
        return redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

class RedisCache(CacheBackend):
    """
    Redis cache backend with optional TTL support.
    Accepts an injectable client for testing or advanced usage.
    """
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, logger=None, client: Optional[RedisClientProtocol] = None, default_ttl: Optional[float] = None):
        self._client = client if client is not None else RedisClientFactory.create(host, port, db)
        self._logger = logger
        self._default_ttl = default_ttl

    def test_connection(self) -> bool:
        """
        Test the connection to the Redis server. Returns True if successful, False otherwise.
        Logs the result.
        """
        try:
            result = self._client.ping()
            if self._logger:
                self._logger.debug("Redis connection successful.")
            return result
        except Exception as e:
            if self._logger:
                self._logger.error(f"Redis connection failed: {e}")
            return False

    def get(self, key: Any) -> Optional[Any]:
        value = self._client.get(key)
        return value

    def set(self, key: Any, value: Any, ttl: Optional[float] = None) -> None:
        use_ttl = ttl if ttl is not None else self._default_ttl
        if use_ttl is not None:
            self._client.setex(key, int(use_ttl), value)
        else:
            self._client.set(key, value)

    def delete(self, key: Any) -> None:
        self._client.delete(key)

    def clear(self) -> None:
        self._client.flushdb()
