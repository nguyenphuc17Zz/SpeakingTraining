import httpx
import pytest

from app.domains.ai.adapters.groq import GroqAdapter
from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AIStreamEventType,
)
from app.domains.ai.errors import ProviderAuthError


@pytest.mark.asyncio
async def test_groq_generate_success():
    mock_response_data = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "model": "llama-3.3-70b-versatile",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "初めまして！どうぞよろしくお願いします。",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 10,
            "total_tokens": 22,
        },
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer gsk_test_key"
        return httpx.Response(200, json=mock_response_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GroqAdapter(transport=transport)

    req = AIRequest(
        messages=[AIMessage(role=AIMessageRole.USER, content="初めまして")],
        model="llama-3.3-70b-versatile",
    )
    resp = await adapter.generate(req, "gsk_test_key")

    assert resp.text == "初めまして！どうぞよろしくお願いします。"
    assert resp.provider == "groq"
    assert resp.model == "llama-3.3-70b-versatile"
    assert resp.usage.input_tokens == 12
    assert resp.usage.output_tokens == 10
    assert resp.usage.total_tokens == 22


@pytest.mark.asyncio
async def test_groq_auth_error():
    mock_error_data = {
        "error": {
            "message": "Invalid API Key provided.",
            "type": "invalid_request_error",
            "code": "invalid_api_key",
        }
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json=mock_error_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GroqAdapter(transport=transport)

    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Test")])
    with pytest.raises(ProviderAuthError):
        await adapter.generate(req, "bad_key")


@pytest.mark.asyncio
async def test_groq_streaming_success():
    sse_body = (
        'data: {"choices": [{"delta": {"content": "お疲れ様"}}]}\n\n'
        'data: {"choices": [{"delta": {"content": "です！"}}], "usage": {"prompt_tokens": 8, "completion_tokens": 6, "total_tokens": 14}}\n\n'
        "data: [DONE]\n\n"
    )

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sse_body.encode(), headers={"content-type": "text/event-stream"})

    transport = httpx.MockTransport(mock_handler)
    adapter = GroqAdapter(transport=transport)

    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Test")])
    events = []
    async for event in adapter.stream(req, "gsk_test"):
        events.append(event)

    text_deltas = [e.text_delta for e in events if e.type == AIStreamEventType.TEXT_DELTA]
    assert "".join(text_deltas) == "お疲れ様です！"


@pytest.mark.asyncio
async def test_groq_list_models():
    mock_models_data = {
        "data": [
            {
                "id": "llama-3.3-70b-versatile",
                "object": "model",
                "active": True,
                "context_window": 128000,
            },
            {
                "id": "llama-3.1-8b-instant",
                "object": "model",
                "active": True,
                "context_window": 128000,
            },
            {
                "id": "deprecated-model",
                "object": "model",
                "active": False,
                "context_window": 8000,
            },
        ]
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert "Bearer gsk_123" in request.headers.get("Authorization", "")
        return httpx.Response(200, json=mock_models_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GroqAdapter(transport=transport)

    models = await adapter.list_models("gsk_123")
    assert len(models) == 2  # Deprecated active=False filtered out
    model_ids = [m.id for m in models]
    assert "llama-3.3-70b-versatile" in model_ids
    assert "llama-3.1-8b-instant" in model_ids
    assert "deprecated-model" not in model_ids
