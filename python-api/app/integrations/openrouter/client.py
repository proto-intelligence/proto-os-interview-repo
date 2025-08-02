"""
Main OpenRouter client implementation with async support.
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Union, Generator
import json
import asyncio
from ..utils.services import create_chat_completion, stream_chat_completion

from .clients import OpenRouterHTTPClient, OpenRouterClientError, OpenRouterAPIError
from .schemas import (
    CompletionRequest,
    CompletionResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    StreamResponse,
    GenerationResponse,
    ModelInfo,
    ModelEndpoint,
    Credits,
)

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Main OpenRouter API client with async support.
    
    This client provides a high-level interface to interact with the OpenRouter API,
    including support for completions, chat completions, streaming, and model management.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the OpenRouter client.
        
        Args:
            api_key: OpenRouter API key (defaults to environment variable)
            timeout: Request timeout in seconds
        """
        self.http_client = OpenRouterHTTPClient(api_key=api_key, timeout=timeout)
    
    async def __aenter__(self):
        """Async context manager entry."""
        asyncio.run(self.http_client.__aenter__())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        asyncio.run(self.http_client.__aexit__(exc_type, exc_val, exc_tb))
    
    async def close(self):
        """Close the client and cleanup resources."""
        asyncio.run(self.http_client.close())
    
    def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Create a text completion.
        
        Args:
            request: Completion request parameters
            
        Returns:
            Completion response
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info(f"Creating completion with model: {request.model}")
            request_json = request.model_dump(exclude_none=True)

            # print(f"\n Requesst: {request_json} \n")
            
            response_data = asyncio.run(self.http_client.post(
                "/completions",
                request_json
            ))
            # print(f"\n Response: {response_data} \n")
            
            logger.debug(f"Completion response received: {response_data.get('id')}")
            return CompletionResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Completion request failed: {e}")
            raise
    
    def chat_completion(
        self,
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Create a chat completion.
        
        Args:
            request: Chat completion request parameters
            
        Returns:
            Chat completion response
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info(f"Creating chat completion with model: {request.model}")
            
            response_data = asyncio.run(self.http_client.post(
                "/chat/completions",
                request.model_dump(exclude_none=True)
            ))
            print(f"Chat completion response received: {response_data}")
            
            logger.debug(f"Chat completion response received: {response_data.get('id')}")
            return ChatCompletionResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Chat completion request failed: {e}")
            return {"id": "", "usage": {}, "choices": []}
    
    def stream_chat_completion(
        self,
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        Create a streaming chat completion.
        
        Args:
            request: Chat completion request parameters
            
        Yields:
            Stream response chunks
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info(f"Creating streaming chat completion with model: {request.model}")
            
            # Ensure streaming is enabled
            request.stream = True

            # The post method returns a coroutine that resolves to an async generator
            # We need to await it to get the actual async generator
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Await the coroutine to get the async generator
            async_gen = loop.run_until_complete(
                self.http_client.post(
                    "/chat/completions",
                    request.model_dump(exclude_none=True),
                    stream=True
                )
            )

            # Use your sync wrapper to convert async generator to sync generator
            for chunk_data in self.sync_wrap_async_gen(async_gen):
                yield StreamResponse(**chunk_data)

            loop.close()
                
        except Exception as e:
            logger.error(f"Streaming chat completion request failed: {e}")
            raise

    def sync_wrap_async_gen(self, async_gen: AsyncGenerator) -> Generator:
        """
        Convert an async generator into a sync generator by running the event loop internally.
        WARNING: Use with caution; better to make the calling function async.
        """
        # Use the existing event loop if available, otherwise create a new one
        try:
            loop = asyncio.get_running_loop()
            # If there's already a running loop, we need to use a different approach
            import concurrent.futures
            
            def run_async_gen():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    agen = async_gen.__aiter__()
                    while True:
                        try:
                            chunk = new_loop.run_until_complete(agen.__anext__())
                            yield chunk
                        except StopAsyncIteration:
                            break
                finally:
                    new_loop.close()
            
            yield from run_async_gen()
            
        except RuntimeError:
            # No running loop, we can create our own
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            agen = async_gen.__aiter__()

            try:
                while True:
                    chunk = loop.run_until_complete(agen.__anext__())
                    yield chunk
            except StopAsyncIteration:
                pass
            finally:
                loop.close()
    
    def chat_completion_with_schema(
        self,
        request: ChatCompletionRequest,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> ChatCompletionResponse:
        """
        Create a chat completion with structured output schema.
        
        Args:
            request: Chat completion request parameters
            response_schema: JSON schema for structured response
            
        Returns:
            Chat completion response with structured output
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info(f"Creating structured chat completion with model: {request.model}")
            
            if response_schema:
                request.response_format = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_response",
                        "schema": response_schema,
                        "strict": True
                    }
                }
            
            response_data = asyncio.run(self.http_client.post(
                "/chat/completions",
                request.model_dump(exclude_none=True)
            ))
            
            logger.debug(f"Structured chat completion response received: {response_data.get('id')}")
            return ChatCompletionResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Structured chat completion request failed: {e}")
            raise
    
    def get_generation(self, generation_id: str) -> GenerationResponse:
        """
        Retrieve a specific generation by ID.
        
        Args:
            generation_id: ID of the generation to retrieve
            
        Returns:
            Generation response
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors (including 404 for not found)
        """
        try:
            logger.info(f"Retrieving generation: {generation_id}")
            
            response_data = asyncio.run(self.http_client.get(
                f"/generation", {"id": generation_id}
            ))
            response_data = response_data.get("data")
            
            print(f"Generation retrieved: {response_data}")
            return GenerationResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Get generation request failed: {e}")
            raise
    
    def list_models(self) -> List[ModelInfo]:
        """
        List all available models.
        
        Returns:
            List of model information
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info("Listing available models")
            
            response_data = asyncio.run(self.http_client.get("/models"))
            
            # Handle both array and object responses
            if isinstance(response_data, list):
                models_data = response_data
            else:
                models_data = response_data.get("data", [])

            # this can be used to extend the models list to get better details of each models
            # models_data = = [self.normalize_model_list_data(model) for model in models_data[:1]]
            # models = [ModelInfo(**model) for model in models_data]
            models = [model.get("id") for model in models_data]
            logger.debug(f"Retrieved {len(models)} models")
            
            return models
            
        except Exception as e:
            logger.error(f"List models request failed: {e}")
            return []

    def normalize_model_list_data(self, raw_model: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure top-level keys exist with fallback values
        raw_model.setdefault("created", None)
        raw_model.setdefault("description", None)
        raw_model.setdefault("canonical_slug", None)
        raw_model.setdefault("context_length", None)
        raw_model.setdefault("hugging_face_id", None)
        raw_model.setdefault("per_request_limits", None)
        raw_model.setdefault("supported_parameters", None)

        # Normalize architecture sub-dictionary
        arch = raw_model.get("architecture") or {}
        if arch:
            arch.setdefault("input_modalities", [])
            arch.setdefault("output_modalities", [])
            arch.setdefault("tokenizer", "")
            arch.setdefault("instruct_type", None)
        raw_model["architecture"] = arch if arch else None

        # Normalize top_provider sub-dictionary
        top_provider = raw_model.get("top_provider") or {}
        if top_provider:
            top_provider.setdefault("is_moderated", False)
            top_provider.setdefault("context_length", 0)
            top_provider.setdefault("max_completion_tokens", 0)
        raw_model["top_provider"] = top_provider if top_provider else None

        # Normalize pricing sub-dictionary
        pricing = raw_model.get("pricing") or {}
        if pricing:
            # Use empty string fallback for all keys, None where you want
            pricing.setdefault("prompt", "")
            pricing.setdefault("completion", "")
            pricing.setdefault("image", "")
            pricing.setdefault("request", "")
            pricing.setdefault("web_search", "")
            pricing.setdefault("internal_reasoning", "")
            pricing.setdefault("input_cache_read", None)
            pricing.setdefault("input_cache_write", None)
        raw_model["pricing"] = pricing if pricing else None

        # Ensure supported_parameters is a list of strings or None
        sp = raw_model.get("supported_parameters")
        if sp is not None and not isinstance(sp, list):
            raw_model["supported_parameters"] = None

        # Ensure per_request_limits is dict or None
        prl = raw_model.get("per_request_limits")
        if prl is not None and not isinstance(prl, dict):
            raw_model["per_request_limits"] = None

        # Convert None or empty string hugging_face_id to None (your choice)
        hf_id = raw_model.get("hugging_face_id")
        if hf_id == "":
            raw_model["hugging_face_id"] = None

        return raw_model
    
    def list_model_endpoints(self, model_id: str) -> List[ModelEndpoint]:
        """
        List endpoints for a specific model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            List of model endpoints
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info(f"Listing endpoints for model: {model_id}")
            
            response_data = asyncio.run(self.http_client.get(
                f"/models/{model_id}/endpoints"
            ))
            
            # Handle both array and object responses
            if isinstance(response_data, list):
                endpoints_data = response_data
            else:
                endpoints_data = response_data.get("data", [])
                
            # endpoints = [ModelEndpoint(**endpoint) for endpoint in endpoints_data]
            endpoints = [ModelEndpoint(**endpoints_data)]
            logger.debug(f"Retrieved endpoints for model {model_id}")
            
            return [endpoints_data]
            
        except Exception as e:
            logger.error(f"List model endpoints request failed: {e}")
            return []
    
    def get_credits(self) -> Credits:
        """
        Get current credit balance and usage information.
        
        Returns:
            Credits information
            
        Raises:
            OpenRouterClientError: For client-side errors
            OpenRouterAPIError: For API errors
        """
        try:
            logger.info("Retrieving credits information")
            
            response = asyncio.run(self.http_client.get("/credits"))
            response_data = response.get("data")
            response_data["credit"] = response_data.pop("total_credits")
            response_data["usage"] = response_data.pop("total_usage")
            # print(f"\n Response in get credits: {response_data}, {response_data.keys()} \n")
            
            logger.debug("Credits information retrieved")
            return Credits(**response_data)
            
        except Exception as e:
            logger.error(f"Get credits request failed: {e}")
            return {}
