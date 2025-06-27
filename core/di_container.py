from dependency_injector import containers, providers
from core.config.config import get_alpha_vantage_api_key
from core.stock_api import stock_api

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_alpha_vantage_api_key)
    fetch_stock_price = providers.Factory(stock_api.fetch_stock_price)
