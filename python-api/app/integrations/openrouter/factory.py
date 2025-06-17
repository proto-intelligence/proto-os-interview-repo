from .client import OpenRouterClient
from .interfaces import LLMProviderInterface

class ProviderFactory:
    def __init__(self):
        self.providers = {
            "openrouter": OpenRouterClient()
        }

    def get_provider(self, name: str) -> LLMProviderInterface:
        provider = self.providers.get(name)
        if not provider:
            raise ValueError(f"Provider '{name}' is not supported.")
        return provider