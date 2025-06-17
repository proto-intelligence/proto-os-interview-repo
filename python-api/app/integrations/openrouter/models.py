from typing import List, Literal, Optional
from pydantic import BaseModel, Field


Role = Literal["user", "assistant", "system"]

class Message(BaseModel):
    role: Role
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stream: Optional[bool] = False


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str]


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]


class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = 256
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)


class CompletionChoice(BaseModel):
    text: str
    index: int
    finish_reason: Optional[str]


class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[CompletionChoice]


class GenerationResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    generation: str
