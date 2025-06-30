import os

def load_llm_prompt() -> str:
    """
    Loads the LLM prompt from the llm_prompt.txt file.
    """
    prompt_path = os.path.join(os.path.dirname(__file__), 'llm_prompt.txt')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read().strip()
