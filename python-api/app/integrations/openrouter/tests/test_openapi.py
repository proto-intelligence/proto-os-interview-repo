from http import HTTPStatus
from fastapi.testclient import TestClient
from main import app

from app.integrations.openrouter.client import OpenRouterClient as openrouter_client

client = TestClient(app)

def test_list_models():
    response = client.get("/api/v1/openapi/models")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)

def test_list_model_endpoints_valid():
    model_id = "openai/gpt-4o"  # usa uno válido que hayas probado
    response = client.get(f"/api/v1/openapi/models/endpoints?model_id={model_id}")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)

def test_list_model_endpoints_invalid(client):
    model_id = "modelo_no_existente"
    response = client.get(f"/models/endpoints?model_id={model_id}")
    assert response.status_code in [HTTPStatus.INTERNAL_SERVER_ERROR, HTTPStatus.NOT_FOUND]

def test_get_generation_valid():
    generation_id = "gen-1750137123-DA3xmuHJYerJSCB3HskM"  # reemplaza con un ID válido generado previamente
    response = client.get(f"/api/v1/openapi/generations?generation_id={generation_id}")
    if response.status_code == 404:
        # puede pasar si no existe el generation_id
        assert response.json()["detail"] == f"Generation ID '{generation_id}' not found."
    else:
        assert response.status_code == HTTPStatus.OK
        assert "id" in response.json()

def test_get_generation_invalid(client):
    generation_id = "no_existe"
    response = client.get(f"/generations?generation_id={generation_id}")
    assert response.status_code in [HTTPStatus.NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR]
    
    
# ---------- /completions ----------

def test_completion_success(client):
    payload = {
        "model": "openai/gpt-4o",
        "prompt": "Hello world",
        "max_tokens": 10
    }
    response = client.post("/api/v1/openapi/completions", json=payload)
    assert response.status_code == HTTPStatus.OK
    assert "choices" in response.json()

def test_completion_error(client):
    payload = {
        "model": "invalid-model",
        "prompt": "Hello",
        "max_tokens": 10
    }
    response = client.post("/api/v1/openapi/completions", json=payload)
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.INTERNAL_SERVER_ERROR]

# ---------- /chat/completions ----------

def test_chat_completion_success(client):
    payload = {
        "model": "openai/gpt-4o",
        "messages": [{"role": "user", "content": "Tell me a joke"}]
    }
    response = client.post("/api/v1/openapi/chat/completions", json=payload)
    assert response.status_code == HTTPStatus.OK
    assert "choices" in response.json()

def test_chat_completion_error(client):
    payload = {
        "model": "",  # Invalid model
        "messages": [{"role": "user", "content": "Tell me something"}]
    }
    response = client.post("/api/v1/openapi/chat/completions", json=payload)
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.INTERNAL_SERVER_ERROR]

# ---------- /chat/completions/stream ----------

def test_chat_completion_stream_success(client):
    payload = {
        "model": "openai/gpt-4o",
        "messages": [{"role": "user", "content": "Short poem"}],
        "stream": True
    }
    response = client.post("/api/v1/openapi/chat/completions/stream", json=payload)
    assert response.status_code == HTTPStatus.OK

def test_chat_completion_stream_error(client):
    payload = {
        "model": "invalid-model",
        "messages": [{"role": "user", "content": "anything"}],
        "stream": True
    }
    response = client.post("/api/v1/openapi/chat/completions/stream", json=payload)
    assert response.headers["content-type"].startswith("text/event-stream")

# ---------- /chat/completions/schema ----------

def test_chat_completion_schema_success(client):
    payload = {
        "model": "openai/gpt-4o",
        "messages": [{"role": "user", "content": "Give me user data"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "UserInfo",
                    "description": "Get information about a user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        },
                        "required": ["name"]
                    }
                }
            }
        ]
    }
    response = client.post("/api/v1/openapi/chat/completions/schema", json=payload)
    assert response.status_code == HTTPStatus.OK
    assert "choices" in response.json()

def test_chat_completion_schema_error(client):
    payload = {
        "model": "",  # invalid model
        "messages": [],
        "tools": []
    }
    response = client.post("/api/v1/openapi/chat/completions/schema", json=payload)
    assert response.status_code in [HTTPStatus.BAD_REQUEST, HTTPStatus.INTERNAL_SERVER_ERROR]

# ---------- /credits ----------

def test_get_credits_success(client):
    response = client.get("/api/v1/openapi/credits")
    assert response.status_code == HTTPStatus.OK
    data = response.json().get("data", {})
    assert isinstance(data, dict)
    assert "total_credits" in data or "credits" in data or "total_granted" in data

def test_get_credits_error(monkeypatch, client):
    # Mock que espera self como primer parámetro
    def mock_get_credits_failure(self):
        raise Exception("Simulated failure")

    # Aplicamos el monkeypatch sobre la clase
    from app.integrations.openrouter import client as openrouter_client
    monkeypatch.setattr(openrouter_client.OpenRouterClient, "get_credits", mock_get_credits_failure)

    response = client.get("/api/v1/openapi/credits")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Simulated failure"