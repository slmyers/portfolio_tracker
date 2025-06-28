import unittest
from unittest.mock import patch, MagicMock
from core.cache.memory import MemoryCache
from core.cache.redis import RedisCache

class TestMemoryCache(unittest.TestCase):
    def setUp(self):
        self.cache = MemoryCache()

    def test_set_and_get(self):
        self.cache.set('foo', 'bar')
        self.assertEqual(self.cache.get('foo'), 'bar')

    def test_ttl_expiry(self):
        self.cache.set('foo', 'bar', ttl=0.01)
        import time
        time.sleep(0.02)
        self.assertIsNone(self.cache.get('foo'))

    def test_delete(self):
        self.cache.set('foo', 'bar')
        self.cache.delete('foo')
        self.assertIsNone(self.cache.get('foo'))

    def test_clear(self):
        self.cache.set('foo', 'bar')
        self.cache.clear()
        self.assertIsNone(self.cache.get('foo'))

class TestRedisCache(unittest.TestCase):
    def test_default_ttl(self):
        mock_client = MagicMock()
        cache = RedisCache(client=mock_client, default_ttl=42)
        cache.set('foo', 'bar')
        mock_client.setex.assert_called_with('foo', 42, 'bar')
    def setUp(self):
        self.mock_client = MagicMock()
        self.cache = RedisCache(client=self.mock_client)

    def test_set_and_get(self):
        self.mock_client.get.return_value = 'bar'
        self.cache.set('foo', 'bar')
        self.cache.get('foo')
        self.mock_client.set.assert_called_with('foo', 'bar')
        self.mock_client.get.assert_called_with('foo')

    def test_set_with_ttl(self):
        self.cache.set('foo', 'bar', ttl=10)
        self.mock_client.setex.assert_called_with('foo', 10, 'bar')

    def test_delete(self):
        self.cache.delete('foo')
        self.mock_client.delete.assert_called_with('foo')

    def test_clear(self):
        self.cache.clear()
        self.mock_client.flushdb.assert_called_once()

    def test_test_connection_success(self):
        mock_logger = MagicMock()
        cache = RedisCache(logger=mock_logger, client=self.mock_client)
        self.mock_client.ping.return_value = True
        self.assertTrue(cache.test_connection())
        self.mock_client.ping.assert_called_once()
        mock_logger.debug.assert_called_with("Redis connection successful.")

    def test_test_connection_failure(self):
        mock_logger = MagicMock()
        cache = RedisCache(logger=mock_logger, client=self.mock_client)
        self.mock_client.ping.side_effect = Exception('fail now')
        self.assertFalse(cache.test_connection())
        mock_logger.error.assert_called()

if __name__ == '__main__':
    unittest.main()
