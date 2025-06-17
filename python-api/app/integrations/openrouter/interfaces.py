from abc import ABC, abstractmethod
from .models import ChatCompletionRequest, ChatCompletionResponse

class LLMProviderInterface(ABC):
    @abstractmethod
    def chat_completion(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        """Realiza una solicitud de chat_completion a un modelo LLM"""
        pass