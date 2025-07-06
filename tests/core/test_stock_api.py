from unittest.mock import patch
from core.integrations import stock_api

def test_fetch_stock_price():
    # Mock requests.get to avoid real API calls
    class MockResponse:
        def json(self):
            return {
                'Time Series (1min)': {
                    '2025-06-27 16:00:00': {'4. close': '123.45'}
                }
            }
    with patch.object(stock_api.requests, 'get', return_value=MockResponse()):
        price = stock_api.fetch_stock_price('AAPL')
    assert price == 123.45

def test_batch_fetch_stock_prices():
    # Mock fetch_stock_price to avoid real API calls
    with patch.object(stock_api, 'fetch_stock_price', side_effect=lambda symbol: 100.0 if symbol == 'AAPL' else 200.0):
        prices = stock_api.batch_fetch_stock_prices(['AAPL', 'GOOG'])
    assert prices == [100.0, 200.0]
