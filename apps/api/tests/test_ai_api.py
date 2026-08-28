import pytest
from httpx import AsyncClient

from app.domains.ai.contracts import AIRequest, AIResponse, AIUsage
from app.domains.ai.health import circuit_breaker_manager
from app.domains.ai.registry import provider_registry


class MockAPIAdapter:
    def __init__(self, provider_id: str):
        self.provider_id = provider_id

    async def generate(self, request: AIRequest, api_key: str) -> AIResponse:
        return AIResponse(
            text="API Route Test Output: こんにちは！",
            model="gemini-1.5-flash",
            provider="gemini",
            usage=AIUsage(input_tokens=20, output_tokens=10, total_tokens=30),
            latency_ms=100,
        )


@pytest.mark.asyncio
async def test_list_providers_and_models(client: AsyncClient):
    resp = await client.get("/api/v1/ai/providers")
    assert resp.status_code == 200
    providers = resp.json()
    assert len(providers) >= 2
    provider_ids = [p["id"] for p in providers]
    assert "gemini" in provider_ids
    assert "groq" in provider_ids

    resp = await client.get("/api/v1/ai/models")
    assert resp.status_code == 200
    models = resp.json()
    assert len(models) >= 4

    # Test filtering by provider
    resp_gemini = await client.get("/api/v1/ai/models?provider=gemini")
    assert resp_gemini.status_code == 200
    gemini_models = resp_gemini.json()
    assert len(gemini_models) >= 2
    for m in gemini_models:
        assert m["provider_id"] == "gemini"

    # Test force refresh endpoint
    refresh_resp = await client.post("/api/v1/ai/models/refresh?provider=gemini")
    assert refresh_resp.status_code == 200
    refreshed = refresh_resp.json()
    assert len(refreshed) >= 2


@pytest.mark.asyncio
async def test_ai_routing_policy_endpoints(client: AsyncClient):
    resp = await client.get("/api/v1/ai/routing")
    assert resp.status_code == 200
    data = resp.json()
    assert data["routing_mode"] in ("auto", "manual")
    assert "fallback_priority" in data

    # Update routing policy
    update_payload = {
        "routing_mode": "manual",
        "preferred_provider": "groq",
        "fallback_enabled": False,
        "fallback_priority": ["groq", "gemini"],
    }
    resp = await client.put("/api/v1/ai/routing", json=update_payload)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["routing_mode"] == "manual"
    assert updated["preferred_provider"] == "groq"
    assert updated["fallback_enabled"] is False


@pytest.mark.asyncio
async def test_ai_generate_endpoint_with_credential(client: AsyncClient):
    # Set credential first
    await client.post(
        "/api/v1/providers/credentials",
        json={"provider": "gemini", "api_key": "dummy_key_for_test"},
    )

    # Register mock adapter
    mock = MockAPIAdapter("gemini")
    provider_registry.register(mock)
    circuit_breaker_manager.reset()

    generate_payload = {
        "messages": [{"role": "user", "content": "テストメッセージ"}],
        "task": "conversation",
        "provider": "gemini",
        "model": "gemini-1.5-flash",
    }
    resp = await client.post("/api/v1/ai/generate", json=generate_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["text"] == "API Route Test Output: こんにちは！"
    assert data["provider"] == "gemini"
    assert data["usage"]["total_tokens"] == 30

    # Verify usage was logged
    usage_resp = await client.get("/api/v1/ai/usage")
    assert usage_resp.status_code == 200
    usage_data = usage_resp.json()
    assert usage_data["total_requests"] >= 1
