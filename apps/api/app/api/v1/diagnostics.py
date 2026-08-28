import platform
import sys
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domains.ai.health import circuit_breaker_manager
from app.domains.ai.registry import ModelRegistry
from app.domains.ai.router import ai_deduplicator
from app.domains.audio.cache import tts_cache
from app.domains.speech.model_manager import whisper_model_manager
from app.infrastructure.database.session import get_db
from app.infrastructure.redis.client import RedisManager, get_redis_manager

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.get("/system", summary="System Health and Resource Diagnostics")
async def get_system_diagnostics(
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis_manager),
) -> dict[str, Any]:
    settings = get_settings()

    # DB Connection Test
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    # Redis Connection Test
    redis_connected = await redis.ping()

    # AI Circuit Breaker Diagnostics
    providers_meta = ModelRegistry.get_all_providers()
    providers_status = {}
    for p in providers_meta:
        providers_status[p.id] = {
            "available": circuit_breaker_manager.is_available(p.id),
        }

    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "database": {
            "engine": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
            "connected": db_connected,
        },
        "redis": {
            "connected": redis_connected,
            "url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL,
        },
        "ai_circuit_breakers": providers_status,
        "speech": {
            "whisper_device": settings.WHISPER_DEVICE,
            "whisper_compute_type": settings.WHISPER_COMPUTE_TYPE,
            "voicevox_url": settings.VOICEVOX_ENGINE_URL,
        },
    }


@router.get("/models", summary="Speech & AI Model Memory Diagnostics")
async def get_model_diagnostics() -> dict[str, Any]:
    return {
        "whisper_models": whisper_model_manager.get_status(),
    }


@router.get("/cache", summary="System Caches Diagnostics")
async def get_cache_diagnostics() -> dict[str, Any]:
    return {
        "tts_cache": tts_cache.get_stats(),
        "ai_deduplicator": {
            "cached_entries": len(ai_deduplicator._cache),
            "max_entries": ai_deduplicator.max_entries,
            "ttl_seconds": ai_deduplicator.ttl_seconds,
        },
    }


@router.post("/cache/clear", summary="Clear In-Memory Caches")
async def clear_caches() -> dict[str, Any]:
    tts_count = tts_cache.size()
    tts_cache.clear()
    ai_deduplicator._cache.clear()
    whisper_evicted = whisper_model_manager.evict_all()

    return {
        "status": "cleared",
        "tts_entries_cleared": tts_count,
        "ai_dedup_cleared": True,
        "whisper_models_evicted": whisper_evicted,
    }
