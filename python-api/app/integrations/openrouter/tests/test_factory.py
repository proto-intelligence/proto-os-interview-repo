import pytest
from app.integrations.openrouter.factory import get_llm_provider
from app.integrations.openrouter.client import OpenRouterClient

def test_get_valid_provider():
    provider = get_llm_provider("openrouter")
    assert isinstance(provider, OpenRouterClient)

def test_get_invalid_provider():
    with pytest.raises(NotImplementedError) as excinfo:
        get_llm_provider("unknown")
    assert "Provider 'unknown' is not supported yet." in str(excinfo.value)