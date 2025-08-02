"""
Test cases for OpenRouter client implementation.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from ...openrouter.client import OpenRouterClient
from ...openrouter.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    StreamResponse,
    GenerationResponse,
    ModelInfo,
    Credits,
    Message,
    Usage,
    ChatCompletionChoice,
    Choice
)


class TestOpenRouterClient:
    """Test cases for OpenRouterClient main functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return OpenRouterClient(api_key="test-api-key")
    
    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        mock_client = Mock()
        mock_client.post = AsyncMock()
        mock_client.get = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.close = AsyncMock()
        return mock_client

    def test_client_initialization(self):
        """Test client initialization with and without API key."""
        # Test with API key
        client = OpenRouterClient(api_key="test-key")
        assert client.http_client is not None
        
        # Test with default timeout
        client = OpenRouterClient()
        assert client.http_client is not None
        
        # Test with custom timeout
        client = OpenRouterClient(timeout=60)
        assert client.http_client is not None

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_completion_success(self, mock_http_class, client):
        """Test successful completion request."""
        # Mock response data
        mock_response = {
            "id": "cmpl-123",
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "object": "text_completion",
            "created": 1234567890,
            "choices": [{
                "text": "This is a test response",
                "finish_reason": "stop",
                "logprobs": None,
                "native_finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
                "cost": 0.001,
                "is_byok": False,
                "prompt_tokens_details": {"cached_tokens": 0},
                "completion_tokens_details": {"reasoning_tokens": 0, "accepted_prediction_tokens": 0}
            }
        }
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.post = AsyncMock(return_value=mock_response)
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Create request
        request = CompletionRequest(
            model="gpt-3.5-turbo",
            prompt="Test prompt"
        )
        
        # Execute
        response = client.completion(request)
        
        # Assertions
        assert isinstance(response, CompletionResponse)
        assert response.id == "cmpl-123"
        assert response.model == "gpt-3.5-turbo"
        assert len(response.choices) == 1
        assert response.choices[0].text == "This is a test response"

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_chat_completion_success(self, mock_http_class, client):
        """Test successful chat completion request."""
        # Mock response data
        mock_response = {
            "id": "chatcmpl-123",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you today?"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
                "cost": 0.002,
                "is_byok": False,
                "prompt_tokens_details": {"cached_tokens": 0},
                "completion_tokens_details": {"reasoning_tokens": 0, "accepted_prediction_tokens": 0}
            }
        }
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.post = AsyncMock(return_value=mock_response)
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Create request
        messages = [
            Message(role="user", content="Hello!")
        ]
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        # Execute
        response = client.chat_completion(request)
        
        # Assertions
        assert isinstance(response, ChatCompletionResponse)
        assert response.id == "chatcmpl-123"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Hello! How can I help you today?"

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_chat_completion_with_schema(self, mock_http_class, client):
        """Test chat completion with structured output schema."""
        # Mock response data
        mock_response = {
            "id": "chatcmpl-schema-123",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": '{"answer": "42", "confidence": 0.95}'
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 10,
                "total_tokens": 25,
                "cost": 0.003,
                "is_byok": False,
                "prompt_tokens_details": {"cached_tokens": 0},
                "completion_tokens_details": {"reasoning_tokens": 0, "accepted_prediction_tokens": 0}
            }
        }
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.post = AsyncMock(return_value=mock_response)
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Create request and schema
        messages = [Message(role="user", content="What is the answer?")]
        request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=messages)
        
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "number"}
            }
        }
        
        # Execute
        response = client.chat_completion_with_schema(request, schema)
        
        # Assertions
        assert isinstance(response, ChatCompletionResponse)
        assert response.id == "chatcmpl-schema-123"
        assert '"answer": "42"' in response.choices[0].message.content

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_stream_chat_completion(self, mock_http_class, client):
        """Test streaming chat completion."""
        # Mock streaming response data
        mock_chunks = [
            {
                "id": "chatcmpl-stream-123",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "gpt-3.5-turbo",
                "choices": [{
                    "index": 0,
                    "delta": {"content": "Hello"},
                    "finish_reason": None
                }]
            },
            {
                "id": "chatcmpl-stream-123",
                "object": "chat.completion.chunk",
                "created": 1234567890,
                "model": "gpt-3.5-turbo",
                "choices": [{
                    "index": 0,
                    "delta": {"content": " there!"},
                    "finish_reason": "stop"
                }]
            }
        ]
        
        # Create async generator mock
        async def mock_async_gen():
            for chunk in mock_chunks:
                yield chunk
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.post = AsyncMock(return_value=mock_async_gen())
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Create request
        messages = [Message(role="user", content="Hello!")]
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )
        
        # Execute and collect chunks
        chunks = list(client.stream_chat_completion(request))
        
        # Assertions
        assert len(chunks) == 2
        assert all(isinstance(chunk, StreamResponse) for chunk in chunks)
        assert chunks[0].choices[0].delta["content"] == "Hello"
        assert chunks[1].choices[0].delta["content"] == " there!"

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_get_generation(self, mock_http_class, client):
        """Test retrieving a specific generation."""
        # Mock response data
        mock_response = {
            "data": {
                "id": "gen-123",
                "model": "gpt-3.5-turbo",
                "created": "2023-12-01T10:00:00Z"
            }
        }
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Execute
        response = client.get_generation("gen-123")
        
        # Assertions
        assert isinstance(response, GenerationResponse)
        assert response.id == "gen-123"
        assert response.model == "gpt-3.5-turbo"

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_list_models(self, mock_http_class, client):
        """Test listing available models."""
        # Mock response data
        mock_response = [
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet"}
        ]
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Execute
        models = client.list_models()
        
        # Assertions
        assert isinstance(models, list)
        assert len(models) == 3
        assert "gpt-3.5-turbo" in models
        assert "gpt-4" in models
        assert "claude-3-sonnet" in models

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_get_credits(self, mock_http_class, client):
        """Test retrieving credits information."""
        # Mock response data
        mock_response = {
            "data": {
                "total_credits": 100.0,
                "total_usage": 25.5
            }
        }
        
        # Setup mock
        mock_http_instance = Mock()
        mock_http_instance.get = AsyncMock(return_value=mock_response)
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Execute
        credits = client.get_credits()
        
        # Assertions
        assert isinstance(credits, Credits)
        assert credits.credit == 100.0
        assert credits.usage == 25.5

    @patch('openrouter.client.OpenRouterHTTPClient')
    def test_chat_completion_error_handling(self, mock_http_class, client):
        """Test error handling in chat completion."""
        # Setup mock to raise exception
        mock_http_instance = Mock()
        mock_http_instance.post = AsyncMock(side_effect=Exception("API Error"))
        mock_http_class.return_value = mock_http_instance
        client.http_client = mock_http_instance
        
        # Create request
        messages = [Message(role="user", content="Hello!")]
        request = ChatCompletionRequest(model="gpt-3.5-turbo", messages=messages)
        
        # Execute - should return empty response instead of raising
        response = client.chat_completion(request)
        
        # Assertions
        assert response["id"] == ""
        assert response["usage"] == {}
        assert response["choices"] == []