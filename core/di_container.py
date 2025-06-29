from dependency_injector import containers, providers
from core.config.config import get_alpha_vantage_api_key, get_postgres_config, get_redis_config
from core.persistence.postgres import PostgresPool
from core.integrations import stock_api

from core.cache import MemoryCache
from core.cache.redis import RedisCache
from core.lock.in_process import InProcessLock
from core.logger import Logger

# Factory function for stock_api with lock
def stock_api_with_lock():
    obj = stock_api
    from core.di_container import Container
    container = Container()
    get_named_lock = container.get_named_lock
    setattr(obj, 'get_named_lock', get_named_lock)
    return obj

# Integrations sub-container
class IntegrationsContainer(containers.DeclarativeContainer):
    stock_api = providers.Factory(stock_api_with_lock)

# Main DI container
class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_alpha_vantage_api_key)
    postgres_config = providers.Singleton(get_postgres_config)
    redis_config = providers.Singleton(get_redis_config)
    integrations = providers.Container(IntegrationsContainer)
    cache = providers.Singleton(MemoryCache)
    redis_cache = providers.Singleton(
        RedisCache,
        host=providers.Callable(lambda c: c.host, redis_config),
        port=providers.Callable(lambda c: c.port, redis_config),
        logger=providers.Singleton(Logger),
    )
    postgres_pool = providers.Singleton(PostgresPool)
    get_named_lock = providers.Factory(lambda name: InProcessLock(name))
    logger = providers.Singleton(Logger)
