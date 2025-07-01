from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from .llm_tools import summarize_positions_tool
from .llm_interface import LLMClient
from typing import TypedDict, List

class LLMState(TypedDict):
    positions: List[dict]
    llm_response: str

class LLMAgent(LLMClient):
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(openai_api_key=api_key)
        self.graph = self._build_graph()

    def _build_graph(self):
        def llm_summary_node(state):
            positions = state["positions"]
            summary_input = summarize_positions_tool(positions)
            prompt = f"""
Below are my Interactive Brokers positions from my portfolio activity report. Please summarize my positions and provide feedback.

Positions:
{summary_input}
"""
            response = self.llm.invoke(prompt)
            return {"llm_response": response.content if hasattr(response, "content") else str(response)}

        state_schema = LLMState
        graph = StateGraph(state_schema)
        graph.add_node("summarize", llm_summary_node)
        graph.set_entry_point("summarize")
        graph.add_edge("summarize", END)
        return graph.compile()

    def summarize_positions(self, positions: list) -> str:
        result = self.graph.invoke({"positions": positions})
        return result["llm_response"]
