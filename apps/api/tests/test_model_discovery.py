import pytest
from app.domains.ai.contracts import AITask, ModelCapability, ModelMetadata
from app.domains.ai.discovery import ModelDiscoveryService


class MockDiscoveryAdapter:
    def __init__(self, provider_id: str, models: list[ModelMetadata]):
        self.provider_id = provider_id
        self.models = models
        self.call_count = 0

    async def list_models(self, api_key: str) -> list[ModelMetadata]:
        self.call_count += 1
        return self.models


@pytest.mark.asyncio
async def test_model_discovery_service_caching():
    discovery = ModelDiscoveryService(ttl_seconds=60.0)

    mock_models = [
        ModelMetadata(
            id="gemini-2.0-flash",
            provider_id="gemini",
            display_name="Gemini 2.0 Flash",
            context_window=1000000,
            capabilities=[ModelCapability.TEXT, ModelCapability.STREAMING],
            is_recommended=True,
        ),
        ModelMetadata(
            id="gemini-1.5-pro",
            provider_id="gemini",
            display_name="Gemini 1.5 Pro",
            context_window=2000000,
            capabilities=[ModelCapability.TEXT, ModelCapability.STREAMING, ModelCapability.REASONING],
            is_recommended=False,
        ),
    ]

    mock_adapter = MockDiscoveryAdapter("gemini", mock_models)

    # Register mock into provider_registry
    from app.domains.ai.registry import provider_registry
    provider_registry.register(mock_adapter)

    # 1. First fetch -> cache miss, calls adapter
    res1 = await discovery.get_models_for_provider("gemini", "test_key", force_refresh=False)
    assert len(res1) == 2
    assert mock_adapter.call_count == 1

    # 2. Second fetch -> cache hit, doesn't call adapter
    res2 = await discovery.get_models_for_provider("gemini", "test_key", force_refresh=False)
    assert len(res2) == 2
    assert mock_adapter.call_count == 1

    # 3. Force refresh -> calls adapter again
    res3 = await discovery.get_models_for_provider("gemini", "test_key", force_refresh=True)
    assert len(res3) == 2
    assert mock_adapter.call_count == 2


@pytest.mark.asyncio
async def test_model_discovery_task_tier_matching():
    discovery = ModelDiscoveryService()

    available = [
        ModelMetadata(
            id="llama-3.1-8b-instant",
            provider_id="groq",
            display_name="Llama 3.1 8B Instant",
            context_window=128000,
            is_recommended=False,
        ),
        ModelMetadata(
            id="llama-3.3-70b-versatile",
            provider_id="groq",
            display_name="Llama 3.3 70B Versatile",
            context_window=128000,
            is_recommended=True,
        ),
    ]

    # Fast tier -> should pick 8b
    fast_model = discovery.get_recommended_model_for_task(
        task=AITask.GRAMMAR_CORRECTION,
        provider_id="groq",
        available_models=available,
    )
    assert fast_model == "llama-3.1-8b-instant"

    # Balanced tier -> should pick 70b
    balanced_model = discovery.get_recommended_model_for_task(
        task=AITask.CONVERSATION,
        provider_id="groq",
        available_models=available,
    )
    assert balanced_model == "llama-3.3-70b-versatile"
