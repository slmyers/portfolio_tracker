from dependency_injector import containers, providers
from core.config.config import get_alpha_vantage_api_key
from core.integrations import stock_api

from core.cache import MemoryCache
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
    integrations = providers.Container(IntegrationsContainer)
    cache = providers.Singleton(MemoryCache)
    get_named_lock = providers.Factory(lambda name: InProcessLock(name))
    logger = providers.Singleton(Logger)
