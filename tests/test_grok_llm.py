import pytest
from core.integrations.llm.grok_llm import GrokLLM

def test_grok_llm_invoke(monkeypatch):
    called = {}
    class MockResponse:
        def raise_for_status(self): pass
        def json(self):
            return {"choices": [{"message": {"content": "Grok mock response"}}]}
    def mock_post(url, headers=None, json=None):
        called['headers'] = headers
        called['url'] = url
        called['json'] = json
        return MockResponse()
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    grok = GrokLLM(api_key="fake-token-123")
    response = grok.invoke("Test prompt")
    assert response.content == "Grok mock response"
    # Assert API key is passed as Bearer token
    assert called['headers']['Authorization'] == "Bearer fake-token-123"
