import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import json
from ..openrouter.schemas import (
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


# Utility functions for common operations
async def create_chat_completion(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> ChatCompletionResponse:
    from .openrouter.client import OpenRouterClient
    """
    Utility function to create a chat completion.
    
    Args:
        model: Model identifier
        messages: List of chat messages
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Returns:
        Chat completion response
    """
    from .schemas import Message
    
    formatted_messages = [Message(**msg) for msg in messages]
    request = ChatCompletionRequest(
        model=model,
        messages=formatted_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    
    async with OpenRouterClient() as client:
        return await client.chat_completion(request)


async def stream_chat_completion(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> AsyncGenerator[StreamResponse, None]:
    """
    Utility function to create a streaming chat completion.
    
    Args:
        model: Model identifier
        messages: List of chat messages
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional parameters
        
    Yields:
        Stream response chunks
    """
    from .schemas import Message
    
    formatted_messages = [Message(**msg) for msg in messages]
    request = ChatCompletionRequest(
        model=model,
        messages=formatted_messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        **kwargs
    )
    
    async with OpenRouterClient() as client:
        async for chunk in client.stream_chat_completion(request):
            yield chunk