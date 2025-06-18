from .client import OpenRouterClient
from .interfaces import LLMProviderInterface

def get_llm_provider(provider: str) -> LLMProviderInterface:
    if provider == "openrouter":
        return OpenRouterClient()
    else:
        raise NotImplementedError(f"Provider '{provider}' is not supported yet.")
