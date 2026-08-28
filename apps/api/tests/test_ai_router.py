import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AIResponse,
    AITask,
    AIUsage,
)
from app.domains.ai.errors import (
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.domains.ai.health import circuit_breaker_manager
from app.domains.ai.registry import provider_registry
from app.domains.ai.router import AIRouter
from app.domains.providers.schemas import CredentialCreate
from app.domains.providers.service import CredentialService
from app.domains.settings.schemas import UserSettingsUpdate
from app.domains.settings.service import SettingsService
from app.domains.users.service import UserService


class MockProviderAdapter:
    def __init__(self, provider_id: str, will_fail: bool = False, error_type: Exception | None = None, response_text: str = "Mock response"):
        self.provider_id = provider_id
        self.will_fail = will_fail
        self.error_type = error_type or ProviderRateLimitError("Rate limit exceeded", provider_id=provider_id)
        self.response_text = response_text
        self.call_count = 0

    async def generate(self, request: AIRequest, api_key: str) -> AIResponse:
        self.call_count += 1
        if self.will_fail:
            raise self.error_type
        return AIResponse(
            text=self.response_text,
            model=request.model or "mock-model",
            provider=self.provider_id,
            usage=AIUsage(input_tokens=10, output_tokens=5, total_tokens=15),
            latency_ms=120,
        )


@pytest.mark.asyncio
async def test_ai_router_auto_primary_success(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    cred_service = CredentialService(db_session)

    # Setup credentials for gemini
    await cred_service.create_credential(CredentialCreate(provider="gemini", api_key="test_gemini_key"), user.id)

    # Mock Gemini
    mock_gemini = MockProviderAdapter("gemini", will_fail=False, response_text="Gemini Konnichiwa")
    provider_registry.register(mock_gemini)
    circuit_breaker_manager.reset()

    router = AIRouter(db_session)
    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Hello")])
    resp = await router.generate(task=AITask.CONVERSATION, request=req, user_id=user.id)

    assert resp.text == "Gemini Konnichiwa"
    assert resp.provider == "gemini"
    assert resp.fallback_occurred is False
    assert mock_gemini.call_count == 1


@pytest.mark.asyncio
async def test_ai_router_fallback_to_secondary_on_rate_limit(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    cred_service = CredentialService(db_session)

    # Setup credentials for gemini and groq
    await cred_service.create_credential(CredentialCreate(provider="gemini", api_key="test_gemini_key"), user.id)
    await cred_service.create_credential(CredentialCreate(provider="groq", api_key="test_groq_key"), user.id)

    # Configure user settings: primary=gemini, priority="gemini,groq"
    settings_service = SettingsService(db_session)
    await settings_service.update_settings(
        UserSettingsUpdate(
            default_ai_provider="gemini",
            routing_mode="auto",
            fallback_enabled=True,
            fallback_priority="gemini,groq",
        ),
        user.id,
    )

    # Gemini fails with 429 RateLimit, Groq succeeds
    mock_gemini = MockProviderAdapter("gemini", will_fail=True, error_type=ProviderRateLimitError("429 TPM Exceeded", provider_id="gemini"))
    mock_groq = MockProviderAdapter("groq", will_fail=False, response_text="Groq Fallback Answer")
    provider_registry.register(mock_gemini)
    provider_registry.register(mock_groq)
    circuit_breaker_manager.reset()

    router = AIRouter(db_session)
    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Hello")])
    resp = await router.generate(task=AITask.CONVERSATION, request=req, user_id=user.id)

    assert resp.text == "Groq Fallback Answer"
    assert resp.provider == "groq"
    assert resp.fallback_occurred is True
    assert mock_gemini.call_count == 1
    assert mock_groq.call_count == 1


@pytest.mark.asyncio
async def test_ai_router_manual_mode_no_fallback_when_disabled(db_session: AsyncSession):
    user_service = UserService(db_session)
    user = await user_service.get_or_create_default_user()
    cred_service = CredentialService(db_session)

    await cred_service.create_credential(CredentialCreate(provider="gemini", api_key="test_gemini_key"), user.id)
    await cred_service.create_credential(CredentialCreate(provider="groq", api_key="test_groq_key"), user.id)

    settings_service = SettingsService(db_session)
    await settings_service.update_settings(
        UserSettingsUpdate(
            default_ai_provider="gemini",
            routing_mode="manual",
            fallback_enabled=False,
        ),
        user.id,
    )

    mock_gemini = MockProviderAdapter("gemini", will_fail=True, error_type=ProviderUnavailableError("503 Down", provider_id="gemini"))
    mock_groq = MockProviderAdapter("groq", will_fail=False, response_text="Groq")
    provider_registry.register(mock_gemini)
    provider_registry.register(mock_groq)
    circuit_breaker_manager.reset()

    router = AIRouter(db_session)
    req = AIRequest(messages=[AIMessage(role=AIMessageRole.USER, content="Hello")])

    with pytest.raises(ProviderUnavailableError):
        await router.generate(task=AITask.CONVERSATION, request=req, user_id=user.id)

    assert mock_gemini.call_count == 1
    assert mock_groq.call_count == 0
