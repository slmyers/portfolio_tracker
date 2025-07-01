import requests

class GrokLLM:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.x.ai/v1/chat/completions"

    def invoke(self, prompt: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "grok-3-latest",
            "messages": [{"role": "user", "content": prompt}]
        }
        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        # Adjust extraction based on Grok's actual API response
        return type("Response", (), {"content": result["choices"][0]["message"]["content"]})()
