"""
Extensible Multi-Provider LLM Framework
Supports plug-and-play integration of multiple LLM providers with centralized
rate-limiting, retry logic, and error reporting.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Type
from contextlib import asynccontextmanager
import aiohttp
import json
from collections import defaultdict, deque


# ============================================================================
# Core Data Models
# ============================================================================

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ProviderType(Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class Message:
    role: MessageRole
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    cached_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass
class LLMRequest:
    model: str
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    provider_specific: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    id: str
    content: str
    model: str
    provider: str
    usage: Usage
    finish_reason: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    name: str
    provider_type: ProviderType
    api_key: str
    base_url: str
    max_requests_per_minute: int = 60
    max_tokens_per_minute: int = 90000
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimiter:
    """Token bucket rate limiter with request and token limits."""
    
    def __init__(self, max_requests_per_minute: int, max_tokens_per_minute: int):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        
        # Request rate limiting
        self.request_tokens = max_requests_per_minute
        self.request_last_update = time.time()
        
        # Token rate limiting
        self.token_bucket = max_tokens_per_minute
        self.token_last_update = time.time()
        
        # Track usage history
        self.request_history = deque(maxlen=100)
        self.token_history = deque(maxlen=100)
        
    def _refill_buckets(self):
        """Refill rate limit buckets based on elapsed time."""
        now = time.time()
        
        # Refill request bucket
        elapsed = now - self.request_last_update
        self.request_tokens = min(
            self.max_requests_per_minute,
            self.request_tokens + (elapsed * self.max_requests_per_minute / 60.0)
        )
        self.request_last_update = now
        
        # Refill token bucket
        elapsed = now - self.token_last_update
        self.token_bucket = min(
            self.max_tokens_per_minute,
            self.token_bucket + (elapsed * self.max_tokens_per_minute / 60.0)
        )
        self.token_last_update = now
    
    async def acquire(self, estimated_tokens: int = 0) -> bool:
        """Acquire permission for a request with estimated token usage."""
        self._refill_buckets()
        
        # Check if we have enough request tokens
        if self.request_tokens < 1:
            return False
            
        # Check if we have enough token capacity
        if estimated_tokens > 0 and self.token_bucket < estimated_tokens:
            return False
            
        # Consume tokens
        self.request_tokens -= 1
        if estimated_tokens > 0:
            self.token_bucket -= estimated_tokens
            
        # Record usage
        now = time.time()
        self.request_history.append(now)
        if estimated_tokens > 0:
            self.token_history.append((now, estimated_tokens))
            
        return True
    
    def get_wait_time(self, estimated_tokens: int = 0) -> float:
        """Calculate how long to wait before the next request."""
        self._refill_buckets()
        
        wait_time = 0.0
        
        # Check request rate limit
        if self.request_tokens < 1:
            wait_time = max(wait_time, (1 - self.request_tokens) * 60.0 / self.max_requests_per_minute)
            
        # Check token rate limit
        if estimated_tokens > 0 and self.token_bucket < estimated_tokens:
            token_wait = (estimated_tokens - self.token_bucket) * 60.0 / self.max_tokens_per_minute
            wait_time = max(wait_time, token_wait)
            
        return wait_time


# ============================================================================
# Error Handling & Reporting
# ============================================================================

class LLMError(Exception):
    def __init__(self, message: str, provider: str, error_type: str = "unknown", 
                 status_code: Optional[int] = None, retry_after: Optional[float] = None):
        super().__init__(message)
        self.provider = provider
        self.error_type = error_type
        self.status_code = status_code
        self.retry_after = retry_after
        self.timestamp = datetime.now()


class ErrorReporter:
    """Centralized error reporting and analytics."""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.provider_health = defaultdict(lambda: {"success": 0, "error": 0, "last_error": None})
        
    def report_error(self, error: LLMError, provider: str, request: LLMRequest):
        """Report an error for tracking and analysis."""
        error_record = {
            "timestamp": error.timestamp,
            "provider": provider,
            "error_type": error.error_type,
            "message": str(error),
            "status_code": error.status_code,
            "model": request.model,
            "retry_after": error.retry_after
        }
        
        self.error_history.append(error_record)
        self.error_counts[f"{provider}:{error.error_type}"] += 1
        self.provider_health[provider]["error"] += 1
        self.provider_health[provider]["last_error"] = error.timestamp
        
        logging.error(f"LLM Error [{provider}]: {error}")
        
    def report_success(self, provider: str):
        """Report a successful request."""
        self.provider_health[provider]["success"] += 1
        
    def get_provider_health(self, provider: str) -> Dict[str, Any]:
        """Get health metrics for a provider."""
        health = self.provider_health[provider]
        total = health["success"] + health["error"]
        
        return {
            "success_rate": health["success"] / total if total > 0 else 0.0,
            "total_requests": total,
            "last_error": health["last_error"],
            "is_healthy": health["success"] > health["error"] * 2  # 2:1 success ratio
        }


# ============================================================================
# Provider Interface
# ============================================================================

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig, error_reporter: ErrorReporter):
        self.config = config
        self.error_reporter = error_reporter
        self.rate_limiter = RateLimiter(
            config.max_requests_per_minute,
            config.max_tokens_per_minute
        )
        
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
        
    @abstractmethod
    def estimate_tokens(self, request: LLMRequest) -> int:
        """Estimate token usage for rate limiting."""
        pass
        
    @abstractmethod
    def format_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Format request for provider's API."""
        pass
        
    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> LLMResponse:
        """Parse provider's response into standard format."""
        pass
        
    async def make_request(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
            async with session.post(url, json=data, headers=headers) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    error_type = "rate_limit" if response.status == 429 else "api_error"
                    retry_after = float(response.headers.get("Retry-After", 0))
                    
                    raise LLMError(
                        f"API request failed: {response_data.get('error', 'Unknown error')}",
                        provider=self.config.name,
                        error_type=error_type,
                        status_code=response.status,
                        retry_after=retry_after
                    )
                    
                return response_data