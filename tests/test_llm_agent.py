import pytest
from core.integrations.llm.llm_agent import LLMAgent

class MockLLM:
    def invoke(self, prompt: str):
        return type("Response", (), {"content": "Mocked summary"})()

def test_summarize_positions_returns_expected_response():
    agent = LLMAgent(llm=MockLLM())
    positions = [{"symbol": "AAPL", "qty": 10}]
    result = agent.summarize_positions(positions)
    assert "Mocked summary" in result
