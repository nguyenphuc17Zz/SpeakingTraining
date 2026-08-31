from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.audio import router as audio_router
from app.api.v1.coach import router as coach_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.diagnostics import router as diagnostics_router
from app.api.v1.game import router as game_router
from app.api.v1.health import router as health_router
from app.api.v1.learner import router as learner_router
from app.api.v1.keigo import router as keigo_router
from app.api.v1.learning import router as learning_router
from app.api.v1.personas import router as personas_router
from app.api.v1.pitch import router as pitch_router
from app.api.v1.monologue import router as monologue_router
from app.api.v1.pronunciation import router as pronunciation_router
from app.api.v1.reflex import router as reflex_router
from app.api.v1.situations import router as situations_router
from app.api.v1.providers import router as providers_router
from app.api.v1.settings import router as settings_router
from app.api.v1.shadowing import router as shadowing_router
from app.api.v1.speech import router as speech_router
from app.api.v1.vocabulary import router as vocabulary_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(diagnostics_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(providers_router)
api_v1_router.include_router(personas_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(speech_router)
api_v1_router.include_router(audio_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(learner_router)
api_v1_router.include_router(learning_router)
api_v1_router.include_router(reflex_router)
api_v1_router.include_router(keigo_router)
api_v1_router.include_router(monologue_router)
api_v1_router.include_router(pitch_router)
api_v1_router.include_router(situations_router)
api_v1_router.include_router(pronunciation_router)
api_v1_router.include_router(shadowing_router)
api_v1_router.include_router(game_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(coach_router)
api_v1_router.include_router(vocabulary_router)
