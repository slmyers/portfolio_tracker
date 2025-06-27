
from dependency_injector import containers, providers
from core.config.config import get_alpha_vantage_api_key
from core.integrations import stock_api

class IntegrationsContainer(containers.DeclarativeContainer):
    stock_api = providers.Object(stock_api)

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_alpha_vantage_api_key)
    integrations = providers.Container(IntegrationsContainer)
