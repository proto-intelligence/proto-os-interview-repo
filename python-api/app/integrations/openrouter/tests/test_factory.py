import pytest
from app.integrations.openrouter.factory import ProviderFactory
from app.integrations.openrouter.client import OpenRouterClient

def test_get_valid_provider():
    factory = ProviderFactory()
    provider = factory.get_provider("openrouter")
    assert isinstance(provider, OpenRouterClient)

def test_get_invalid_provider():
    factory = ProviderFactory()
    with pytest.raises(ValueError) as excinfo:
        factory.get_provider("unknown")
    assert "Provider 'unknown' is not supported." in str(excinfo.value)