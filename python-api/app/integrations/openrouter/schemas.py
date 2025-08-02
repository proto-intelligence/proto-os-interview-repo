"""
Pydantic models for OpenRouter API requests and responses.
"""
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class Usage(BaseModel):
    include: Optional[bool] = Field(default=None, description="Whether to include usage information in the response")


class CompletionRequest(BaseModel):
    model: str = Field(..., description="The model ID to use. If unspecified, the user's default is used.")
    prompt: str = Field(..., description="The text prompt to complete")
    usage: Optional[Usage] = Field(default=None, description="Whether to include usage information in the response")
    transforms: Optional[List[str]] = Field(default=None, description="List of prompt transforms (OpenRouter-only)")
    stream: Optional[bool] = Field(default=False, description="Enable streaming of results")
    max_tokens: Optional[int] = Field(default=512, ge=1, description="Maximum number of tokens")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    seed: Optional[int] = Field(default=0, description="Seed for deterministic outputs")
    top_p: Optional[float] = Field(default=0.8, gt=0, le=1, description="Top-p sampling value")
    top_k: Optional[int] = Field(default=None, ge=1, description="Top-k sampling value")
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2, le=2, description="Presence penalty")
    repetition_penalty: Optional[float] = Field(default=1.0, gt=0, le=2, description="Repetition penalty")

class ReasoningDetail(BaseModel):
    type: str
    summary: Optional[str] = None
    format: Optional[str] = None
    data: Optional[str] = None
    id: Optional[str] = None


class Choice(BaseModel):
    logprobs: Optional[Any]
    finish_reason: Optional[str]
    native_finish_reason: Optional[str]
    text: str
    reasoning: Optional[str] = None
    reasoning_details: Optional[List[ReasoningDetail]] = None


class PromptTokensDetails(BaseModel):
    cached_tokens: Optional[int] = 0


class CompletionTokensDetails(BaseModel):
    reasoning_tokens: Optional[int] = 0
    accepted_prediction_tokens: Optional[int] = 0


class Usage(BaseModel):
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    total_tokens: Optional[int] = 0
    cost: Optional[float] = 0.0
    is_byok: Optional[bool] = False
    prompt_tokens_details: PromptTokensDetails
    completion_tokens_details: CompletionTokensDetails


class CompletionResponse(BaseModel):
    """Response model for text completion."""
    id: str
    provider: str
    model: str
    object: str
    created: int
    choices: List[Choice]
    usage: Usage


class Message(BaseModel):
    """Chat message model."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str

class ChatCompletionRequest(BaseModel):
    """Request model for chat completion."""
    model: str = Field(..., description="Model identifier")
    messages: List[Message] = Field(..., description="Chat messages")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(0.0, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(0.0, description="Presence penalty")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    stream: Optional[bool] = Field(False, description="Enable streaming")


class ChatCompletionChoice(BaseModel):
    """Chat completion choice model."""
    index: int
    message: Message = {}
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion."""
    id: str
    choices: List[ChatCompletionChoice]
    usage: Usage
    
    model_config = ConfigDict(extra="allow")


class StreamChoice(BaseModel):
    """Streaming choice model."""
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None
    logprobs: Optional[Dict[str, Any]] = None


class StreamResponse(BaseModel):
    """Streaming response model."""
    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]
    usage: Optional[Usage] = None
    system_fingerprint: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


class GenerationResponse(BaseModel):
    """Response model for generation retrieval."""
    id: str
    model: Optional[str] = ""
    created: Optional[str] = ""
    
    model_config = ConfigDict(extra="allow")


# Below schemas can be used to extend the details in the listing of models
class ArchitectureInfo(BaseModel):
    input_modalities: Optional[List[str]] = []
    output_modalities: Optional[List[str]] = []
    tokenizer: Optional[str] = ""
    instruct_type: Optional[str] = None
    modality: Optional[str] = None

class TopProviderInfo(BaseModel):
    is_moderated: Optional[bool] = False
    context_length: Optional[int] = 0
    max_completion_tokens: Optional[int] = 0

class PricingInfo(BaseModel):
    prompt: str
    completion: str
    image: Optional[str] = ""
    request: Optional[str] = ""
    web_search: Optional[str] = ""
    audio: Optional[str] = None
    internal_reasoning: Optional[str] = ""
    input_cache_read: Optional[str] = None
    input_cache_write: Optional[str] = None
    discount: Optional[float] = None

class ModelInfoDetailed(BaseModel):
    id: str
    name: str
    created: Optional[int] = None
    description: Optional[str] = None
    architecture: Optional[ArchitectureInfo] = None
    top_provider: Optional[TopProviderInfo] = None
    pricing: Optional[PricingInfo] = None
    canonical_slug: Optional[str] = None
    context_length: Optional[int] = None
    hugging_face_id: Optional[str] = None
    per_request_limits: Optional[Dict[str, Any]] = None
    supported_parameters: Optional[List[str]] = None

    model_config = ConfigDict(extra="allow")

# end of models to enrich models info

class ModelInfo(BaseModel):
    id: str

    model_config = ConfigDict(extra="allow")


class EndpointInfo(BaseModel):
    name: Optional[str] = None
    context_length: Optional[int] = None
    pricing: Optional[PricingInfo] = None
    provider_name: Optional[str] = None
    tag: Optional[str] = None
    quantization: Optional[str] = None  # Can be None or string
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    supported_parameters: Optional[List[str]] = None
    status: Optional[int] = None
    uptime_last_30m: Optional[float] = None

    model_config = ConfigDict(extra="allow")


class ModelEndpoint(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    created: Optional[int] = None
    description: Optional[str] = None
    architecture: Optional[ArchitectureInfo] = None
    endpoints: Optional[List[EndpointInfo]] = None

    model_config = ConfigDict(extra="allow")


class Credits(BaseModel):
    """Credits information."""
    credit: float
    usage: float = 0.0

    model_config = ConfigDict(extra="allow")


class OpenRouterError(BaseModel):
    """OpenRouter API error response."""
    error: Dict[str, Any]
    
    model_config = ConfigDict(extra="allow")