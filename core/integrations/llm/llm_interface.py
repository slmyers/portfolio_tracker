from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def summarize_positions(self, positions: list) -> str:
        pass
