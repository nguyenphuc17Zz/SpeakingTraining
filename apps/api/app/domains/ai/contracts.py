from collections.abc import AsyncIterator
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.domains.providers.contracts import ModelCapability, ModelMetadata, ProviderMetadata


class AITask(str, Enum):
    CONVERSATION = "conversation"
    DEEP_ANALYSIS = "deep_analysis"
    CONVERSATION_ANALYSIS = "conversation_analysis"
    GRAMMAR_ANALYSIS = "grammar_analysis"
    NATURALNESS_ANALYSIS = "naturalness_analysis"
    CONTEXT_ANALYSIS = "context_analysis"
    FEEDBACK_PRIORITIZATION = "feedback_prioritization"
    SESSION_ANALYSIS = "session_analysis"
    GRAMMAR_CORRECTION = "grammar_correction"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    CURRICULUM = "curriculum"
    EXERCISE_GENERATION = "exercise_generation"
    EXERCISE_EVALUATION = "exercise_evaluation"
    REFLEX_GENERATION = "reflex_generation"
    REFLEX_EVALUATION = "reflex_evaluation"
    KEIGO_GENERATION = "keigo_generation"
    KEIGO_EVALUATION = "keigo_evaluation"
    PITCH_GENERATION = "pitch_generation"
    PITCH_EVALUATION = "pitch_evaluation"
    PITCH_FEEDBACK = "pitch_feedback"
    SITUATIONAL_GENERATION = "situational_generation"
    SITUATIONAL_EVALUATION = "situational_evaluation"
    RECOMMENDATION_EXPLANATION = "recommendation_explanation"
    SPEECH_GENERATION = "speech_generation"
    SPEECH_COHERENCE = "speech_coherence"
    SPEECH_RELEVANCE = "speech_relevance"
    SPEECH_NATURALNESS = "speech_naturalness"
    SPEECH_EVALUATION = "speech_evaluation"
    SPEECH_NATIVE_UPGRADE = "speech_native_upgrade"
    MEMORY = "memory"
    PRONUNCIATION_ANALYSIS = "pronunciation_analysis"
    VIDEO_ANALYSIS = "video_analysis"
    SHADOWING_ANALYSIS = "shadowing_analysis"
    SHADOWING_RECOMMENDATION = "shadowing_recommendation"
    COACH = "coach"
    COACH_CHAT = "coach_chat"
    COACH_EXPLANATION = "coach_explanation"
    COACH_INSIGHT = "coach_insight"
    COACH_PLAN = "coach_plan"
    COACH_SEMANTIC_ANALYSIS = "coach_semantic_analysis"
    COACH_NATIVE_UPGRADE = "coach_native_upgrade"
    WEEKLY_REVIEW = "weekly_review"
    INSIGHT_EXPLANATION = "insight_explanation"
    VOCABULARY_LOOKUP = "vocabulary_lookup"
    PLAYGROUND = "playground"
    GENERAL = "general"


class AIMessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class AIMessage(BaseModel):
    role: AIMessageRole = AIMessageRole.USER
    content: str
    name: str | None = None
    audio_bytes: bytes | None = None
    image_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseFormatType(str, Enum):
    TEXT = "text"
    JSON_OBJECT = "json_object"
    JSON_SCHEMA = "json_schema"


class ResponseFormat(BaseModel):
    type: ResponseFormatType = ResponseFormatType.TEXT
    json_schema: dict[str, Any] | None = None


class AIRequest(BaseModel):
    messages: list[AIMessage]
    task: AITask = AITask.GENERAL
    model: str | None = None
    provider: str | None = None
    temperature: float = 0.7
    max_output_tokens: int | None = None
    system_instruction: str | None = None
    response_format: ResponseFormat | None = None
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cached_tokens: int | None = None
    reasoning_tokens: int | None = None
    estimated_cost_usd: float | None = None


class AIResponse(BaseModel):
    text: str
    model: str
    provider: str
    usage: AIUsage = Field(default_factory=AIUsage)
    finish_reason: str | None = "stop"
    latency_ms: int = 0
    fallback_occurred: bool = False
    attempt_history: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIStreamEventType(str, Enum):
    STARTED = "started"
    TEXT_DELTA = "text_delta"
    USAGE = "usage"
    COMPLETED = "completed"
    ERROR = "error"


class AIStreamEvent(BaseModel):
    type: AIStreamEventType
    text_delta: str | None = None
    usage: AIUsage | None = None
    provider: str | None = None
    model: str | None = None
    finish_reason: str | None = None
    error: str | None = None
    fallback_occurred: bool = False
    latency_ms: int | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"


class ProviderHealth(BaseModel):
    provider_id: str
    status: ProviderHealthStatus = ProviderHealthStatus.NOT_CONFIGURED
    is_configured: bool = False
    latency_ms: int | None = None
    last_checked_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIProvider(Protocol):
    """Protocol for AI LLM Provider Adapters (Gemini, Groq, OpenRouter)."""

    provider_id: str

    async def generate(self, request: AIRequest, api_key: str) -> AIResponse:
        ...

    async def stream(self, request: AIRequest, api_key: str) -> AsyncIterator[AIStreamEvent]:
        ...

    async def test_connection(self, api_key: str) -> ProviderHealth:
        ...

    async def list_models(self, api_key: str) -> list[ModelMetadata]:
        ...


__all__ = [
    "AITask",
    "AIMessageRole",
    "AIMessage",
    "ResponseFormatType",
    "ResponseFormat",
    "AIRequest",
    "AIUsage",
    "AIResponse",
    "AIStreamEventType",
    "AIStreamEvent",
    "ProviderHealthStatus",
    "ProviderHealth",
    "AIProvider",
    "ModelCapability",
    "ModelMetadata",
    "ProviderMetadata",
]

