import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import logger

# Active API Engine & Micro-Domain Registry
from app.domains.personas.service import PersonaService
from app.domains.settings.service import SettingsService
from app.domains.users.service import UserService
from app.infrastructure.database.base import Base
from app.infrastructure.database.session import AsyncSessionLocal, engine
from app.infrastructure.database.sync_schema import sync_database_schema
from app.infrastructure.redis.client import redis_manager
from app.shared.errors.handlers import register_error_handlers

from app.domains.analytics.worker import analytics_worker
from app.domains.conversation_intelligence.worker import analysis_worker
from app.domains.gamification.seeds import GamificationSeeder
from app.domains.gamification.worker import game_worker
from app.domains.learner_memory.worker import learner_memory_worker
from app.domains.learning.worker import learning_worker
from app.domains.pronunciation.worker import pronunciation_worker
from app.domains.shadowing.worker import shadowing_worker
# Bootstrap AI Coach Core tools (side-effect registers tools)
import app.domains.coach.tools_impl  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")

    # Ensure tables exist and schema is up to date
    await sync_database_schema(engine)

    # Seed system personas, default user/settings, and gamification definitions
    async with AsyncSessionLocal() as session:
        persona_service = PersonaService(session)
        await persona_service.seed_system_personas()

        user_service = UserService(session)
        user = await user_service.get_or_create_default_user()

        settings_service = SettingsService(session)
        await settings_service.get_or_create_settings(user.id)

        await GamificationSeeder.seed_defaults(session)
        logger.info(f"Database initialized. Default user ID: {user.id}")

    # Start background analysis, learner memory, learning, pronunciation, shadowing, game & analytics workers
    analysis_worker.start()
    learner_memory_worker.start()
    learning_worker.start()
    pronunciation_worker.start()
    shadowing_worker.start()
    game_worker.start()
    analytics_worker.start()

    # Pre-warm default Whisper STT model in background so first user speech scoring is immediate
    try:
        import asyncio
        from app.domains.speech.model_manager import whisper_model_manager
        default_model = getattr(settings, "WHISPER_DEFAULT_MODEL", "base")
        logger.info(f"Initiating background pre-warm for Whisper model '{default_model}'...")
        asyncio.create_task(
            asyncio.to_thread(whisper_model_manager.get_or_load_model, default_model)
        )
    except Exception as we:
        logger.warning(f"Whisper background pre-warm task failed to start: {we}")

    yield

    logger.info("Shutting down application...")
    await analytics_worker.stop()
    await game_worker.stop()
    await shadowing_worker.stop()
    await pronunciation_worker.stop()
    await learning_worker.stop()
    await learner_memory_worker.stop()
    await analysis_worker.stop()
    await redis_manager.close()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Backend API for Japanese Speaking AI Training OS",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — localhost only (single-user dev)
    # Log effective origins for debugging
    logger.info(f"CORS allow_origins: {settings.cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and Timing Middleware
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"

        logger.info(
            f"[{request_id[:8]}] {request.method} {request.url.path} -> {response.status_code} ({process_time_ms:.2f}ms)"
        )
        return response

    # Register centralized error handlers
    register_error_handlers(app)

    # Include routes
    app.include_router(api_v1_router)

    return app


app = create_app()
