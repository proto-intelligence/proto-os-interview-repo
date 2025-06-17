# integrations/openrouter/client.py

import os
import json
import logging
import requests
from dotenv import load_dotenv

from typing import List

from app.integrations.openrouter.models import *

# Load .env variables
load_dotenv()

# set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self, base_url: str = "https://openrouter.ai/api/v1"):
        self.base_url = base_url
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("Missing OPENROUTER_API_KEY in environment variables.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def post(self, endpoint: str, payload: dict, stream: bool = False):
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload, stream=stream)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def completion(self, payload: CompletionRequest) -> CompletionResponse:
        response = self.post("/completions", payload.dict())
        return CompletionResponse(**response.json())

    def chat_completion(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        response = self.post("/chat/completions", payload.dict())
        return ChatCompletionResponse(**response.json())

    def stream_chat_completion(self, payload: ChatCompletionRequest):
        response = self.post("/chat/completions", payload.dict(), stream=True)
        for line in response.iter_lines():
            if line:
                decoded = json.loads(line.decode("utf-8"))
                yield decoded

    def get_generation(self, generation_id: str) -> GenerationResponse:
        response = requests.get(
            f"{self.base_url}/generations/{generation_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return GenerationResponse(**response.json())

    def list_models(self) -> List[str]:
        response = requests.get(
            f"{self.base_url}/models",
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        return [model["id"] for model in data.get("data", [])]

    def list_model_endpoints(self, model_id: str) -> List[str]:
        response = requests.get(
            f"{self.base_url}/models/{model_id}/endpoints",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json().get("endpoints", [])

    def get_credits(self) -> dict:
        response = requests.get(
            f"{self.base_url}/credits",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()