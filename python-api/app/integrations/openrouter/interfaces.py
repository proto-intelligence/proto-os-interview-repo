from abc import ABC, abstractmethod
from typing import List, Generator, Union
from .schemas import (
    CompletionRequest, CompletionResponse,
    ChatCompletionRequest, ChatCompletionResponse,
    GenerationResponse
)

class LLMProviderInterface(ABC):
    @abstractmethod
    def completion(self, payload: CompletionRequest) -> CompletionResponse:
        pass

    @abstractmethod
    def chat_completion(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        pass

    @abstractmethod
    def stream_chat_completion(self, payload: ChatCompletionRequest) -> Generator[Union[dict, ChatCompletionResponse], None, None]:
        pass

    @abstractmethod
    def get_generation(self, generation_id: str) -> GenerationResponse:
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        pass

    @abstractmethod
    def list_model_endpoints(self, model_id: str) -> List[str]:
        pass

    @abstractmethod
    def get_credits(self) -> dict:
        pass
