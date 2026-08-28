import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AIResponse, AITask, AIUsage
from app.domains.ai.router import AIRequestDeduplicator, PromptBudgetGuard, ai_deduplicator
from app.domains.ai.registry import ModelRegistry, TaskTier
from app.domains.ai.service import AIUsageService
from app.domains.audio.cache import InMemoryTTSCache, TTSCacheKey, tts_cache
from app.domains.audio.contracts import TTSResult
from app.domains.conversation.context import ContextBudgetManager
from app.domains.conversation.models import ConversationTurn
from app.domains.speech.model_manager import WhisperModelManager


# ---------------------------------------------------------------------------
# 1. Whisper Model Manager Tests
# ---------------------------------------------------------------------------

def test_whisper_model_manager_hardware_detection():
    device, compute = WhisperModelManager.detect_hardware("auto", "auto")
    assert device in ("cuda", "cpu")
    assert compute in ("float16", "int8")


def test_whisper_model_manager_lru_eviction():
    import sys
    manager = WhisperModelManager(max_loaded_models=2)

    mock_whisper_pkg = MagicMock()
    mock_whisper_pkg.WhisperModel.side_effect = lambda model_size_or_path, **kwargs: f"model_{model_size_or_path}"

    with patch.dict(sys.modules, {"faster_whisper": mock_whisper_pkg}):
        m1 = manager.get_or_load_model("tiny", device="cpu", compute_type="int8")
        assert m1 == "model_tiny"
        assert len(manager._models) == 1

        m2 = manager.get_or_load_model("base", device="cpu", compute_type="int8")
        assert m2 == "model_base"
        assert len(manager._models) == 2

        # Loading 3rd model should evict oldest (tiny)
        m3 = manager.get_or_load_model("small", device="cpu", compute_type="int8")
        assert m3 == "model_small"
        assert len(manager._models) == 2
        assert ("tiny", "cpu", "int8") not in manager._models
        assert ("base", "cpu", "int8") in manager._models
        assert ("small", "cpu", "int8") in manager._models

        status = manager.get_status()
        assert status["loaded_models_count"] == 2
        assert status["max_loaded_models"] == 2


# ---------------------------------------------------------------------------
# 2. Context Budget & Character Guard Tests
# ---------------------------------------------------------------------------

def test_context_budget_trim_learner_context():
    short_ctx = "<learner_memory>Short context</learner_memory>"
    assert ContextBudgetManager.trim_learner_context(short_ctx) == short_ctx

    long_ctx = "<learner_memory>" + "あ" * 1200 + "</learner_memory>"
    trimmed = ContextBudgetManager.trim_learner_context(long_ctx)
    assert len(trimmed) <= ContextBudgetManager.MAX_LEARNER_CONTEXT_CHARS + 50
    assert "..." in trimmed


def test_context_budget_select_budgeted_turns():
    turns = [
        ConversationTurn(sequence=i, speaker="user" if i % 2 == 0 else "assistant", transcript=f"Turn content {i} " + "X" * 100)
        for i in range(15)
    ]

    selected = ContextBudgetManager.select_budgeted_turns(turns, max_turns=8)
    assert len(selected) <= 8
    # Ensure recency (last turns kept)
    assert selected[-1].sequence == 14


# ---------------------------------------------------------------------------
# 3. Prompt Budget Guard & Task Tiers
# ---------------------------------------------------------------------------

def test_task_tier_mapping():
    assert ModelRegistry.get_task_tier(AITask.GRAMMAR_CORRECTION) == TaskTier.FAST
    assert ModelRegistry.get_task_tier(AITask.CONVERSATION) == TaskTier.BALANCED
    assert ModelRegistry.get_task_tier(AITask.DEEP_ANALYSIS) == TaskTier.DEEP


def test_prompt_budget_guard_trimming():
    huge_messages = [
        AIMessage(role=AIMessageRole.SYSTEM, content="System instruction"),
    ] + [
        AIMessage(role=AIMessageRole.USER, content="A" * 1500) for _ in range(10)
    ]

    req = AIRequest(task=AITask.CONVERSATION, messages=huge_messages)
    PromptBudgetGuard.inspect_and_guard(req, AITask.CONVERSATION)
    # Excessive messages should be pruned
    assert len(req.messages) <= 6


# ---------------------------------------------------------------------------
# 4. AI Request Deduplication Cache
# ---------------------------------------------------------------------------

def test_ai_request_deduplicator():
    dedup = AIRequestDeduplicator(ttl_seconds=5.0, max_entries=10)
    req = AIRequest(
        task=AITask.TRANSLATION,
        messages=[AIMessage(role=AIMessageRole.USER, content="Konnichiwa")],
    )

    key = dedup.compute_key(req, AITask.TRANSLATION, "user_123")
    assert dedup.get(key) is None

    sample_resp = AIResponse(
        text="Hello",
        model="gemini-1.5-flash",
        provider="gemini",
        usage=AIUsage(total_tokens=10),
    )
    dedup.put(key, sample_resp)

    cached = dedup.get(key)
    assert cached is not None
    assert cached.text == "Hello"
    assert cached.metadata.get("cached_response") is True


# ---------------------------------------------------------------------------
# 5. TTS Cache Stats & Memory Byte Tracking
# ---------------------------------------------------------------------------

def test_tts_cache_stats():
    cache = InMemoryTTSCache(max_entries=10, default_ttl_seconds=300.0)
    key = TTSCacheKey.create("こんにちは", "voicevox", "1")

    res = TTSResult(
        text="こんにちは",
        audio_bytes=b"dummy_wav_bytes_12345",
        audio_format="wav",
        provider="voicevox",
        voice_id="1",
    )
    cache.put(key, res)

    hit = cache.get(key)
    assert hit is not None
    assert hit.is_cached is True

    stats = cache.get_stats()
    assert stats["entries"] == 1
    assert stats["hits"] == 1
    assert stats["approx_audio_bytes"] == len(b"dummy_wav_bytes_12345")


# ---------------------------------------------------------------------------
# 6. Database Usage Aggregation (Async DB Test)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ai_usage_service_aggregation(db_session):
    service = AIUsageService(db_session)
    user_id = "test_user_usage_opt"

    # Record two usage records
    await service.record_usage(
        user_id=user_id,
        request_id="req_1",
        provider="gemini",
        model="gemini-1.5-flash",
        task="conversation",
        latency_ms=250,
        usage=AIUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        success=True,
    )
    await service.record_usage(
        user_id=user_id,
        request_id="req_2",
        provider="gemini",
        model="gemini-1.5-flash",
        task="conversation",
        latency_ms=350,
        usage=AIUsage(input_tokens=200, output_tokens=80, total_tokens=280),
        success=True,
    )

    summary = await service.get_usage_summary(user_id=user_id, limit=10)
    assert summary.total_requests == 2
    assert summary.successful_requests == 2
    assert summary.failed_requests == 0
    assert summary.total_input_tokens == 300
    assert summary.total_output_tokens == 130
    assert summary.total_tokens == 430
    assert summary.avg_latency_ms == 300.0
    assert len(summary.recent_records) == 2
