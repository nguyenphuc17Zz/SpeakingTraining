from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    PronunciationFeedbackItem,
    PronunciationResult,
    ReferenceType,
    TargetType,
)


class PronunciationAnalyzeRequest(BaseModel):
    audio_base64: str = Field(description="Base64 encoded WAV audio bytes.")
    target_text: str = Field(description="Target Japanese Kanji/Kana sentence or word.")
    expected_reading: str | None = Field(default=None, description="Optional canonical reading.")
    target_type: TargetType = Field(default=TargetType.SENTENCE)
    reference_type: ReferenceType = Field(default=ReferenceType.SYNTHETIC)
    voicevox_speaker_id: int | None = Field(default=1)
    session_id: str | None = Field(default=None)
    turn_id: str | None = Field(default=None)


class PronunciationAttemptResponse(BaseModel):
    id: str
    user_id: str
    session_id: str | None = None
    turn_id: str | None = None
    reference_text: str
    expected_reading: str | None = None
    user_text: str | None = None
    target_type: str
    reference_type: str
    analysis_status: str
    overall_score: float | None = None
    overall_confidence: str | None = None
    score_interpretation: str | None = None
    engine_version: str = "1.0.0"
    result: PronunciationResult | None = None
    top_issues: list[PronunciationFeedbackItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    practice_recommendation: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class PronunciationPracticeTargetDTO(BaseModel):
    id: str
    target_text: str
    target_reading: str
    target_type: str
    difficulty: str
    weak_area_key: str
    category: str
    hint: str | None = None


class PronunciationHistoryItemDTO(BaseModel):
    id: str
    reference_text: str
    target_type: str
    overall_score: float | None
    score_interpretation: str | None
    analysis_status: str
    created_at: datetime


class PronunciationSummaryStatsDTO(BaseModel):
    total_attempts: int
    avg_overall_score: float
    avg_mora_score: float
    avg_pitch_score: float
    avg_phoneme_score: float
    top_weaknesses: list[str]
    recent_trend: str  # improving, stable, new
