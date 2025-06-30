from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from .llm_tools import generic_tool
from .llm_interface import LLMClient

class LLMAgent(LLMClient):
    def __init__(self, api_key: str, prompt: str):
        self.llm = ChatOpenAI(openai_api_key=api_key)
        self.agent = initialize_agent(
            [generic_tool],
            self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            prompt=prompt,
        )

    def generate_text(self, prompt: str, **kwargs) -> str:
        return self.agent.run(prompt)
