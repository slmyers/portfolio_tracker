from langgraph.graph import StateGraph, END
from .llm_tools import summarize_positions_tool
from .llm_prompt import load_llm_prompt
from .llm_interface import LLMClient
from typing import TypedDict, List

class LLMState(TypedDict):
    positions: List[dict]
    llm_response: str


class LLMAgent(LLMClient):
    def __init__(self, llm):
        """
        llm: Any object with an .invoke(prompt) method (e.g., ChatOpenAI, Anthropic, etc.)
        """
        self.llm = llm
        self.graph = self._build_graph()

    def _build_graph(self):
        llm_prompt = load_llm_prompt()
        def llm_summary_node(state):
            positions = state["positions"]
            summary_input = summarize_positions_tool(positions)
            prompt = llm_prompt.format(positions=summary_input)
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
