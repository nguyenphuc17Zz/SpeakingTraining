from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.redis.client import RedisManager, get_redis_manager
from app.domains.analytics.worker import analytics_worker
from app.domains.conversation_intelligence.worker import analysis_worker
from app.domains.gamification.worker import game_worker
from app.domains.learner_memory.worker import learner_memory_worker
from app.domains.learning.worker import learning_worker
from app.domains.pronunciation.worker import pronunciation_worker
from app.domains.shadowing.worker import shadowing_worker
from app.domains.speech.model_manager import whisper_model_manager
from app.domains.audio.cache import tts_cache

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="General API Health")
async def check_general_health():
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }


@router.get("/live", summary="Liveness Probe")
async def check_liveness():
    """Returns 200 if the process is responsive."""
    return {"status": "alive"}


@router.get("/ready", summary="Readiness Probe")
async def check_readiness(
    db: AsyncSession = Depends(get_db),
    redis: RedisManager = Depends(get_redis_manager),
):
    """Returns 200 if core dependencies (Database and background workers) are active and ready."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    workers_active = all([
        analysis_worker.is_running,
        learner_memory_worker.is_running,
        learning_worker.is_running,
        pronunciation_worker.is_running,
        shadowing_worker.is_running,
        game_worker.is_running,
        analytics_worker.is_running,
    ])

    redis_connected = await redis.ping()

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": False,
                "workers": workers_active,
                "redis": redis_connected,
            },
        )

    return {
        "status": "ready" if workers_active else "degraded",
        "database": True,
        "workers": workers_active,
        "redis": redis_connected,
    }


@router.get("/workers", summary="Worker Status Breakdown")
async def check_workers_status():
    """Returns detailed status and job processing metrics for each background worker."""
    workers = {
        "analysis_worker": {
            "running": analysis_worker.is_running,
            "jobs_processed": analysis_worker.jobs_processed,
            "jobs_failed": analysis_worker.jobs_failed,
        },
        "learner_memory_worker": {
            "running": learner_memory_worker.is_running,
            "jobs_processed": learner_memory_worker.jobs_processed,
            "jobs_failed": learner_memory_worker.jobs_failed,
        },
        "learning_worker": {
            "running": learning_worker.is_running,
            "jobs_processed": learning_worker.jobs_processed,
            "jobs_failed": learning_worker.jobs_failed,
        },
        "pronunciation_worker": {
            "running": pronunciation_worker.is_running,
            "jobs_processed": pronunciation_worker.jobs_processed,
            "jobs_failed": pronunciation_worker.jobs_failed,
        },
        "shadowing_worker": {
            "running": shadowing_worker.is_running,
            "jobs_processed": shadowing_worker.jobs_processed,
            "jobs_failed": shadowing_worker.jobs_failed,
        },
        "game_worker": {
            "running": game_worker.is_running,
            "jobs_processed": game_worker.jobs_processed,
            "jobs_failed": game_worker.jobs_failed,
        },
        "analytics_worker": {
            "running": analytics_worker.is_running,
            "jobs_processed": analytics_worker.jobs_processed,
            "jobs_failed": analytics_worker.jobs_failed,
        },
    }

    total_processed = sum(w["jobs_processed"] for w in workers.values())
    total_failed = sum(w["jobs_failed"] for w in workers.values())

    return {
        "status": "all_running" if all(w["running"] for w in workers.values()) else "partial",
        "total_jobs_processed": total_processed,
        "total_jobs_failed": total_failed,
        "workers": workers,
    }


@router.get("/db", summary="Database Health Check")
async def check_db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "component": "database",
            "connected": True,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "component": "database",
                "connected": False,
                "error": str(e),
            },
        )


@router.get("/redis", summary="Redis Health Check")
async def check_redis_health(redis: RedisManager = Depends(get_redis_manager)):
    connected = await redis.ping()
    if connected:
        return {
            "status": "healthy",
            "component": "redis",
            "connected": True,
        }
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "degraded",
            "component": "redis",
            "connected": False,
            "message": "Redis is unreachable or optional in local mode. System running with in-memory fallback.",
        },
    )
