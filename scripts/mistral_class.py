import requests

class MistralAPI:
    
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.mistral.ai/v1/chat/completions"

        self.PROMPT_URL_TRANLSATION_EN = "Traduis cette Url en anglais et retourne uniquement le résultat traduit, sans explication ni texte supplémentaire : '%s'"
        self.PROMPT_URL_TRANLSATION_ES = "Traduis cette Url en espagnol et retourne uniquement le résultat traduit, sans explication ni texte supplémentaire : '%s'"

    def call(self, prompt, param, model="mistral-tiny", temperature=0.7, max_tokens=100):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt % param}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]

