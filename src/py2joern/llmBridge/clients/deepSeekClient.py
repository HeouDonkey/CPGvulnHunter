class DeepseekClient:
    """
    Client for DeepSeek API.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def query(self, prompt: str):
        import requests
        url = f"{self.base_url}/query"
        response = requests.post(url, headers=self.get_headers(), json={"prompt": prompt})
        response.raise_for_status()
        return response.json()