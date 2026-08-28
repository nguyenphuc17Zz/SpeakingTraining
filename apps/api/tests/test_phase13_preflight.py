"""
Unit tests for Phase 13 — Preflight, Schema Synchronization, and System Readiness.
"""

import pytest
from sqlalchemy import text
from app.infrastructure.database.session import engine
from app.infrastructure.database.sync_schema import sync_database_schema
from app.domains.speech.model_manager import whisper_model_manager
from app.domains.ai.registry import ModelRegistry


@pytest.mark.asyncio
async def test_sync_database_schema():
    """Verify that sync_database_schema runs idempotently without error."""
    await sync_database_schema(engine)
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT 1"))
        assert res.scalar() == 1


def test_ai_task_tier_recommendations():
    """Verify that all task tiers map to valid production models."""
    fast = ModelRegistry.get_recommended_model_for_task("fast_correction", "groq")
    assert fast == "llama-3.3-70b-versatile"

    conv = ModelRegistry.get_recommended_model_for_task("conversation", "gemini")
    assert conv == "gemini-2.0-flash"

    deep = ModelRegistry.get_recommended_model_for_task("session_analysis", "gemini")
    assert deep == "gemini-1.5-pro"


def test_whisper_model_hardware_resolution():
    """Verify hardware detection returns valid device/compute types."""
    device, compute = whisper_model_manager.detect_hardware("auto", "auto")
    assert device in ("cpu", "cuda")
    assert compute in ("int8", "float16", "float32")
