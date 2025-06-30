from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        pass
