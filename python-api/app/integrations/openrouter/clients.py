"""
HTTP client implementations for OpenRouter API calls.
"""
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterHTTPClient:
    """Simplified async HTTP client for OpenRouter API calls using AsyncOpenAI."""
   
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the HTTP client.
       
        Args:
            api_key: OpenRouter API key (defaults to environment variable)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        print(f"\n API Key: {self.api_key} \n")
       
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
       
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
            timeout=timeout
        )
   
    async def __aenter__(self):
        """Async context manager entry."""
        return self
   
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
   
    async def close(self):
        """Close the HTTP client."""
        await self.client.close()
   
    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        stream: bool = False
    ) -> Any:
        """
        Make a POST request.
       
        Args:
            endpoint: API endpoint (e.g., "/chat/completions")
            data: Request payload
            stream: Whether to stream the response
           
        Returns:
            Response data or async generator for streaming
        """
        try:
            if endpoint == "/chat/completions":
                if stream:
                    return self._stream_chat_completion(data)
                else:
                    return await self._chat_completion(data)
            else:
                # For other endpoints, use the raw HTTP client
                return await self._make_raw_request("POST", endpoint, data, stream)
               
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise OpenRouterClientError(f"Request failed: {e}") from e
   
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request.
       
        Args:
            endpoint: API endpoint
            params: Query parameters
           
        Returns:
            Response data
        """
        try:
            if endpoint == "/models":
                response = await self.client.models.list()
                return {"data": [model.dict() for model in response.data]}
            elif endpoint == "/generation":
                return await self._make_raw_request("GET", endpoint, params=params)
            else:
                # For other endpoints, use the raw HTTP client
                return await self._make_raw_request("GET", endpoint, data=params)
               
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise OpenRouterClientError(f"Request failed: {e}") from e
   
    async def _chat_completion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat completion request."""
        response = await self.client.chat.completions.create(**data)
        return response.dict()
   
    async def _stream_chat_completion(self, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming chat completion request."""
        data["stream"] = True
        stream = await self.client.chat.completions.create(**data)
       
        async for chunk in stream:
            yield chunk.dict()
   
    async def _make_raw_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Any:
        """Fallback for endpoints not directly supported by AsyncOpenAI."""
        import aiohttp
        import json
       
        url = f"https://openrouter.ai/api/v1{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
       
        if stream and data:
            data["stream"] = True
       
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(
                method,
                url,
                json=data,
                params=params
            ) as response:
                if not response.ok:
                    response_text = await response.text()
                    logger.error(f"API error {response.status}: {response_text}")
                    try:
                        error_data = json.loads(response_text)
                        raise OpenRouterAPIError(
                            message=error_data.get("error", {}).get("message", "Unknown error"),
                            status_code=response.status,
                            error_data=error_data
                        )
                    except json.JSONDecodeError:
                        raise OpenRouterAPIError(
                            message=response_text,
                            status_code=response.status
                        )
               
                if stream:
                    return self._parse_stream_response(response)
                else:
                    response_text = await response.text()
                    return json.loads(response_text)
   
    async def _parse_stream_response(self, response) -> AsyncGenerator[Dict[str, Any], None]:
        """Parse streaming response."""
        import json
       
        async for line in response.content:
            line = line.decode('utf-8').strip()
            if line.startswith('data: '):
                data_str = line[6:]  # Remove 'data: ' prefix
                if data_str == '[DONE]':
                    break
                try:
                    chunk_data = json.loads(data_str)
                    yield chunk_data
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse streaming chunk: {data_str}")
                    continue


class OpenRouterClientError(Exception):
    """Base exception for OpenRouter client errors."""
    pass


class OpenRouterAPIError(OpenRouterClientError):
    """Exception for OpenRouter API errors."""
   
    def __init__(
        self,
        message: str,
        status_code: int,
        error_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_data = error_data or {}
   
    def __str__(self):
        return f"OpenRouter API Error {self.status_code}: {self.message}"