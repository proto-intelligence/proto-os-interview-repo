from unittest.mock import patch, MagicMock
from app.integrations.openrouter.client import OpenRouterClient
from app.integrations.openrouter.models import ChatCompletionRequest, Message

@patch("integrations.openrouter.client.requests.post")
def test_chat_completion_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1111111,
        "model": "openai/gpt-4o",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello!"
            },
            "finish_reason": "stop"
        }]
    }
    mock_post.return_value = mock_response

    client = OpenRouterClient()
    request_data = ChatCompletionRequest(
        model="openai/gpt-4o",
        messages=[Message(role="user", content="Hi")]
    )
    response = client.chat_completion(request_data)

    assert response.id == "chatcmpl-123"
    assert response.choices[0].message.content == "Hello!"
    assert response.model == "openai/gpt-4o"