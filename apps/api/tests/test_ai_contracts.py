from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AITask,
    ResponseFormat,
    ResponseFormatType,
)
from app.domains.ai.errors import (
    ProviderAuthError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.domains.ai.prompts import get_prompt_template
from app.domains.ai.registry import ModelRegistry, provider_registry


def test_ai_request_normalization():
    req = AIRequest(
        messages=[
            AIMessage(role=AIMessageRole.SYSTEM, content="You are a sensei."),
            AIMessage(role=AIMessageRole.USER, content="こんにちは"),
        ],
        task=AITask.CONVERSATION,
        temperature=0.8,
        response_format=ResponseFormat(type=ResponseFormatType.TEXT),
    )
    assert len(req.messages) == 2
    assert req.task == AITask.CONVERSATION
    assert req.temperature == 0.8
    assert req.stream is False


def test_prompt_template_rendering():
    tmpl = get_prompt_template("basic_conversation")
    assert tmpl is not None
    messages = tmpl.build_messages(
        context={"persona_name": "Yuki", "speaking_style": "Friendly", "difficulty": "N3"},
        user_input="今日はお元気ですか？",
    )
    assert len(messages) == 2
    assert "Yuki" in messages[0].content
    assert "N3" in messages[0].content
    assert messages[1].content == "今日はお元気ですか？"


def test_error_taxonomy_retryability():
    auth_err = ProviderAuthError("Bad key", provider_id="gemini")
    assert auth_err.is_retryable is False
    assert auth_err.status_code == 401

    rate_err = ProviderRateLimitError("Rate limit hit", provider_id="groq")
    assert rate_err.is_retryable is True
    assert rate_err.status_code == 429

    quota_err = ProviderQuotaError("Quota exceeded", provider_id="gemini")
    assert quota_err.is_retryable is True  # retryable via fallback

    timeout_err = ProviderTimeoutError("Timed out", provider_id="openrouter")
    assert timeout_err.is_retryable is True

    unavail_err = ProviderUnavailableError("503 Server Error", provider_id="gemini")
    assert unavail_err.is_retryable is True


def test_registry_resolution():
    assert provider_registry.has_provider("gemini")
    assert provider_registry.has_provider("groq")
    assert provider_registry.has_provider("openrouter")

    gemini_default = ModelRegistry.get_default_model("gemini")
    assert "gemini" in gemini_default

    rec_model = ModelRegistry.get_recommended_model_for_task(AITask.DEEP_ANALYSIS, "gemini")
    assert "1.5-pro" in rec_model
