from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConversationSessionCreate(BaseModel):
    persona_id: str
    mode: str = "conversation"  # 'conversation' | 'coaching'
    provider_preference: str | None = None
    model_preference: str | None = None
    stt_provider_preference: str | None = None
    stt_model_preference: str | None = None
    tts_provider_preference: str | None = None
    tts_voice_preference: str | None = None


class ScaffoldingSuggestion(BaseModel):
    intent: str = "positive"
    ja: str
    vi: str


class ScaffoldingVocab(BaseModel):
    ja: str
    reading: str | None = None
    vi: str


class TurnScaffolding(BaseModel):
    suggestions: list[ScaffoldingSuggestion] = []
    key_vocab: list[ScaffoldingVocab] = []


class ConversationTurnRead(BaseModel):
    id: str
    session_id: str
    sequence: int
    speaker: str  # 'user' | 'assistant'
    transcript: str
    client_turn_id: str | None = None
    stt_provider: str | None = None
    stt_model: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    tts_provider: str | None = None
    tts_voice: str | None = None
    processing_time_ms: int | None = None
    metrics: dict[str, Any] | None = None
    feedback_hint: str | None = None
    scaffolding: TurnScaffolding | dict[str, Any] | None = None
    started_at: datetime
    ended_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def _fill_scaffolding_from_metrics(self) -> "ConversationTurnRead":
        """Ensure scaffolding is populated from metrics even if ORM @property is not read."""
        if self.scaffolding is None and isinstance(self.metrics, dict):
            raw = self.metrics.get("scaffolding")
            if raw and isinstance(raw, dict):
                self.scaffolding = raw
        return self


class ConversationTurnCreate(BaseModel):
    transcript: str
    client_turn_id: str | None = None


class ConversationSessionRead(BaseModel):
    id: str
    user_id: str
    persona_id: str
    mode: str
    status: str
    provider_preference: str | None = None
    model_preference: str | None = None
    stt_provider_preference: str | None = None
    stt_model_preference: str | None = None
    tts_provider_preference: str | None = None
    tts_voice_preference: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    created_at: datetime
    updated_at: datetime
    turns: list[ConversationTurnRead] = []
    opening_audio_base64: str | None = None
    opening_audio_format: str = "wav"

    model_config = ConfigDict(from_attributes=True)


class AudioTurnResponse(BaseModel):
    session_id: str
    user_turn: ConversationTurnRead
    assistant_turn: ConversationTurnRead
    audio_base64: str | None = None
    audio_format: str = "wav"
    metrics: dict[str, Any] = Field(default_factory=dict)
    tts_error: str | None = None


class ConversationSessionSummary(BaseModel):
    session_id: str
    persona_id: str
    persona_name: str
    mode: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int
    turn_count: int
    user_turns_count: int
    assistant_turns_count: int
    total_speaking_time_seconds: float
    avg_turn_latency_ms: float
    primary_ai_provider: str | None = None
    primary_ai_model: str | None = None


class ConversationRecentSessionRead(BaseModel):
    id: str
    persona_id: str
    persona_name: str
    persona_avatar_url: str | None = None
    mode: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int
    turns_count: int
    score: int | None = None
    topic: str | None = None

    model_config = ConfigDict(from_attributes=True)
