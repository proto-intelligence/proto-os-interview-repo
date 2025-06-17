import os
import json
import logging
from fastapi import HTTPException
import requests
from dotenv import load_dotenv
from typing import List, Generator, Union

from app.integrations.openrouter.schemas import (
    CompletionRequest,
    CompletionResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    GenerationResponse
)
from app.integrations.utils.parse_json import parse_structured_output

# Load environment variables
load_dotenv()

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenRouterClient")


class OpenRouterClient:
    """
    Client wrapper for interacting with OpenRouter API.
    Supports /completions, /chat/completions, model listing, generation retrieval, and credit checks.
    """

    def __init__(self, base_url: str = "https://openrouter.ai/api/v1"):
        self.base_url = base_url
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("Missing OPENROUTER_API_KEY in environment variables.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _handle_response(self, response: requests.Response) -> dict:
        """
        Parses the response or raises appropriate exceptions.
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            if response.status_code == 404:
                raise HTTPException(
                status_code=response.status_code,
                detail="Not found"
            )
            logger.error(f"HTTP error: {http_err} | Status code: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )
        except json.JSONDecodeError as decode_err:
            logger.error(f"Failed to parse JSON response: {decode_err}")
            raise
        except Exception as err:
            logger.error(f"Unexpected error: {err}")
            raise

    def _post(self, endpoint: str, payload: dict, stream: bool = False) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload, stream=stream)
            return response
        except requests.RequestException as e:
            logger.exception(f"POST request to {url} failed: {e}")
            raise

    def completion(self, payload: CompletionRequest) -> CompletionResponse:
        """
        Sends a text completion request and parses response.
        """
        response = self._post("/completions", payload.model_dump(exclude_none=True))
        data = self._handle_response(response)
        return CompletionResponse(**data)

    def chat_completion(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Sends a chat completion request and parses response.
        """
        response = self._post("/chat/completions", payload.model_dump(exclude_none=True))
        data = self._handle_response(response)
        return ChatCompletionResponse(**data)

    def stream_chat_completion(self, payload: ChatCompletionRequest) -> Generator[Union[dict, ChatCompletionResponse], None, None]:
        """
        Sends a chat completion request in streaming mode. Yields decoded chunks.
        """
        response = self._post("/chat/completions", payload.model_dump(exclude_none=True), stream=True)
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8").strip()
                    if decoded_line.startswith("data: "):
                        data = decoded_line[len("data: "):]
                        if data == "[DONE]":
                            break
                        try:
                            decoded = json.loads(data)
                            yield decoded
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON: {data}")
        except Exception as e:
            logger.exception("Error during streaming chat completion.")
            raise
        
    def chat_completion_with_schema(self, payload: ChatCompletionRequest) -> dict:
        """
        Sends a chat completion request with JSON Schema-based structured output.
        Returns the structured data as a Python dict.
        """
        response = self._post("/chat/completions", payload.model_dump(exclude_none=True))
        json_data = response.json()

        # La respuesta estructurada está en choices[0].message.content como dict
        structured_output = parse_structured_output(json_data)
        return structured_output

    def get_generation(self, generation_id: str) -> GenerationResponse:
        """
        Retrieves a previously generated result by its ID from OpenRouter.
        """
        url = f"{self.base_url}/generation"  # no /generations/{id}, sino ?id=...
        params = {"id": generation_id}
        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = self._handle_response(response)
            return GenerationResponse(**data["data"])  # la info viene dentro de "data"
        except Exception as e:
            logger.exception(f"Failed to retrieve generation with ID {generation_id}")
            raise

    def list_models(self) -> List[str]:
        """
        Lists all available model identifiers.
        """
        url = f"{self.base_url}/models"
        try:
            response = requests.get(url, headers=self.headers)
            data = self._handle_response(response)
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            logger.exception("Failed to list models.")
            raise

    def list_model_endpoints(self, model_id: str) -> List[str]:
        """
        Lists all endpoints available for a specific model.
        """
        url = f"{self.base_url}/models/{model_id}/endpoints"
        try:
            response = requests.get(url, headers=self.headers)
            handeled_response = self._handle_response(response)
            data = handeled_response.get("data", [])
            return data.get("endpoints", [])
        except Exception as e:
            logger.exception(f"Failed to list endpoints for model {model_id}.")
            raise

    def get_credits(self) -> dict:
        """
        Returns current credit balance or usage quota.
        """
        url = f"{self.base_url}/credits"
        try:
            response = requests.get(url, headers=self.headers)
            return self._handle_response(response)
        except Exception as e:
            logger.exception("Failed to retrieve credit information.")
            raise