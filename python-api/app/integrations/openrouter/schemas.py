from typing import List, Literal, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# Literal role values for chat messages
Role = Literal["user", "assistant", "system"]

# ---- Message Model ----
class Message(BaseModel):
    """
    Represents a single message in the conversation for chat completion.
    """
    role: Role
    content: str


# ---- Response Format Models (for structured outputs) ----
class JsonSchemaDefinition(BaseModel):
    """
    Defines the structure of a strict JSON schema for structured responses.
    """
    name: str
    strict: bool = True
    schema: Dict


class ResponseFormat(BaseModel):
    """
    Used to enforce structured responses from compatible models.
    """
    type: Literal["json_schema"]
    json_schema: JsonSchemaDefinition


# ---- Completion Request Model (Text Completion) ----
class CompletionRequest(BaseModel):
    """
    Request body for OpenRouter /completions endpoint.
    """
    model: str
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: Optional[bool] = False
    seed: Optional[int] = None
    top_k: Optional[int] = Field(default=None, ge=1)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    repetition_penalty: Optional[float] = Field(default=None, gt=0.0, lt=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    top_logprobs: Optional[int] = None
    min_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_a: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    user: Optional[str] = None


# ---- Completion Response Model ----
class CompletionChoice(BaseModel):
    text: str
    finish_reason: Optional[str] = None
    index: Optional[int] = None
    logprobs: Optional[dict] = None
    reasoning: Optional[Union[dict, str]] = None  # ← Aquí está el ajuste


class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[CompletionChoice]
    provider: Optional[str] = None
    usage: Optional[dict] = None


# ---- Chat Completion Request Model ----
class ChatCompletionRequest(BaseModel):
    """
    Request body for OpenRouter /chat/completions endpoint.
    """
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: Optional[bool] = False
    seed: Optional[int] = None
    top_k: Optional[int] = Field(default=None, ge=1)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    repetition_penalty: Optional[float] = Field(default=None, gt=0.0, lt=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    top_logprobs: Optional[int] = None
    min_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top_a: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    user: Optional[str] = None
    response_format: Optional[ResponseFormat] = None


# ---- Chat Completion Response Model ----
class ChatCompletionChoice(BaseModel):
    """
    A single generated message from a chat completion.
    """
    index: int
    message: Message
    finish_reason: Optional[str] = None


class ChatCompletionResponse(BaseModel):
    """
    Response from the /chat/completions endpoint.
    """
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    

class GenerationResponse(BaseModel):
    id: str
    total_cost: Optional[float] = None
    created_at: str
    model: str
    origin: Optional[str] = None
    usage: Optional[float] = None
    is_byok: Optional[bool] = None
    upstream_id: Optional[str] = None
    cache_discount: Optional[float] = None
    app_id: Optional[int] = None
    streamed: Optional[bool] = None
    cancelled: Optional[bool] = None
    provider_name: Optional[str] = None
    latency: Optional[float] = None
    moderation_latency: Optional[float] = None
    generation_time: Optional[float] = None
    finish_reason: Optional[str] = None
    native_finish_reason: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    native_tokens_prompt: Optional[int] = None
    native_tokens_completion: Optional[int] = None
    native_tokens_reasoning: Optional[int] = None
    native_tokens_cached: Optional[int] = None
    num_media_prompt: Optional[int] = None
    num_media_completion: Optional[int] = None
    num_search_results: Optional[int] = None

        

class WeatherSchema(BaseModel):
    location: str
    temperature: float
    conditions: str