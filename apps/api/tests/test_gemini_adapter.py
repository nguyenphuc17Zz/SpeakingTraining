import httpx
import pytest

from app.domains.ai.adapters.gemini import GeminiAdapter
from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AIStreamEventType,
)


@pytest.mark.asyncio
async def test_gemini_generate_success():
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "こんにちは！元気ですか？"}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 15,
            "candidatesTokenCount": 8,
            "totalTokenCount": 23,
        },
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert "x-goog-api-key" in request.headers
        assert request.headers["x-goog-api-key"] == "test_key_123"
        return httpx.Response(200, json=mock_response_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GeminiAdapter(transport=transport)

    req = AIRequest(
        messages=[AIMessage(role=AIMessageRole.USER, content="こんにちは")],
        model="gemini-1.5-flash",
    )
    resp = await adapter.generate(req, "test_key_123")

    assert resp.text == "こんにちは！元気ですか？"
    assert resp.provider == "gemini"
    assert resp.model == "gemini-1.5-flash"
    assert resp.usage.input_tokens == 15
    assert resp.usage.output_tokens == 8
    assert resp.usage.total_tokens == 23


@pytest.mark.asyncio
async def test_gemini_auth_error():
    mock_error_data = {
        "error": {
            "code": 400,
            "message": "API key not valid. Please pass a valid API key.",
            "status": "INVALID_ARGUMENT",
        }
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json=mock_error_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GeminiAdapter(transport=transport)

    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Test")])
    with pytest.raises(Exception):
        await adapter.generate(req, "invalid_key")


@pytest.mark.asyncio
async def test_gemini_rate_limit_error():
    mock_error_data = {
        "error": {
            "code": 429,
            "message": "Resource has been exhausted (e.g. check quota).",
            "status": "RESOURCE_EXHAUSTED",
        }
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json=mock_error_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GeminiAdapter(transport=transport)

    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Test")])
    with pytest.raises(Exception) as exc_info:
        await adapter.generate(req, "key_429")
    assert "exhausted" in str(exc_info.value) or "Rate limit" in str(exc_info.value) or "Quota" in str(exc_info.value)


@pytest.mark.asyncio
async def test_gemini_streaming_success():
    sse_body = (
        'data: {"candidates": [{"content": {"parts": [{"text": "はい、"}]}}]}\n\n'
        'data: {"candidates": [{"content": {"parts": [{"text": "分かりました。"}]}}], "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 6, "totalTokenCount": 16}}\n\n'
        "data: [DONE]\n\n"
    )

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=sse_body.encode(), headers={"content-type": "text/event-stream"})

    transport = httpx.MockTransport(mock_handler)
    adapter = GeminiAdapter(transport=transport)

    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Test")])
    events = []
    async for event in adapter.stream(req, "test_key_stream"):
        events.append(event)

    text_deltas = [e.text_delta for e in events if e.type == AIStreamEventType.TEXT_DELTA]
    assert "".join(text_deltas) == "はい、分かりました。"


@pytest.mark.asyncio
async def test_gemini_clean_model_prefix_handling():
    called_urls = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        called_urls.append(str(request.url))
        return httpx.Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "OK"}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 2, "totalTokenCount": 7},
            },
        )

    transport = httpx.MockTransport(mock_handler)
    adapter = GeminiAdapter(transport=transport)

    # Pass with 'models/' prefix
    req = AIRequest(
        messages=[AIMessage(role=AIMessageRole.USER, content="Hello")],
        model="models/gemini-1.5-flash",
    )
    resp = await adapter.generate(req, "test_key")
    assert resp.model == "gemini-1.5-flash"
    assert "models/gemini-1.5-flash:generateContent" in called_urls[0]
    assert "models/models/" not in called_urls[0]


@pytest.mark.asyncio
async def test_gemini_list_models():
    mock_models_data = {
        "models": [
            {
                "name": "models/gemini-2.0-flash",
                "displayName": "Gemini 2.0 Flash",
                "description": "Next generation fast multimodal model",
                "inputTokenLimit": 1048576,
                "outputTokenLimit": 8192,
                "supportedGenerationMethods": ["generateContent", "countTokens"],
            },
            {
                "name": "models/gemini-1.5-pro",
                "displayName": "Gemini 1.5 Pro",
                "description": "Mid-size multimodal model",
                "inputTokenLimit": 2097152,
                "outputTokenLimit": 8192,
                "supportedGenerationMethods": ["generateContent", "countTokens"],
            },
            {
                "name": "models/text-embedding-004",
                "displayName": "Text Embedding 004",
                "description": "Embedding model",
                "inputTokenLimit": 2048,
                "supportedGenerationMethods": ["embedContent"],
            },
        ]
    }

    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert "x-goog-api-key" in request.headers
        assert str(request.url).startswith("https://generativelanguage.googleapis.com/v1beta/models")
        return httpx.Response(200, json=mock_models_data)

    transport = httpx.MockTransport(mock_handler)
    adapter = GeminiAdapter(transport=transport)

    models = await adapter.list_models("test_key_abc")
    assert len(models) == 2  # Embedding model filtered out
    model_ids = [m.id for m in models]
    assert "gemini-2.0-flash" in model_ids
    assert "gemini-1.5-pro" in model_ids
    assert "text-embedding-004" not in model_ids

    flash_model = next(m for m in models if m.id == "gemini-2.0-flash")
    assert flash_model.context_window == 1048576
    assert flash_model.is_recommended is True
