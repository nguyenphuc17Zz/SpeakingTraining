from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    AnalysisJobStatus,
    CorrectionCategory,
    CorrectionSeverity,
    FeedbackRating,
)


class AnalysisCorrectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    turn_analysis_id: str
    category: CorrectionCategory
    severity: CorrectionSeverity
    severity_score: int
    original: str
    corrected: str
    explanation: str
    native_alternative: str | None = None
    acceptable_alternatives: list[str] | None = None
    context_note: str | None = None
    confidence: AnalysisConfidence
    created_at: datetime


class GrammarNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    grammar_pattern: str
    user_usage: str
    correct_usage: str
    short_explanation: str
    example_sentence: str | None = None


class VocabularyNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_word: str
    suggested_alternatives: list[str] | None = None
    nuance_explanation: str
    jlpt_level: str | None = None


class TurnAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    turn_id: str
    session_id: str
    overall_quality_score: int
    communicative_success: bool
    is_suspicious_transcript: bool
    strengths: list[str] | None = None
    context_notes: list[dict[str, Any]] | None = None
    corrections: list[AnalysisCorrectionRead] = Field(default_factory=list)
    grammar_notes: list[GrammarNoteRead] = Field(default_factory=list)
    vocabulary_notes: list[VocabularyNoteRead] = Field(default_factory=list)
    prompt_version: str
    analyzer_version: str
    ai_provider: str | None = None
    ai_model: str | None = None
    created_at: datetime


class SessionAnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    overall_score: int
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    repeated_issues: list[dict[str, Any]] | None = None
    top_recommendations: list[str] | None = None
    total_user_turns_analyzed: int
    total_corrections_count: int
    must_fix_count: int
    should_fix_count: int
    native_alt_count: int
    grammar_summary: list[str] | None = None
    vocabulary_summary: list[str] | None = None
    prompt_version: str
    analyzer_version: str
    ai_provider: str | None = None
    ai_model: str | None = None
    created_at: datetime


class AnalysisJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: str
    status: AnalysisJobStatus
    session_id: str
    turn_id: str | None = None
    attempts: int
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class AnalysisFeedbackCreate(BaseModel):
    rating: FeedbackRating
    reason: str | None = None
    turn_analysis_id: str | None = None
    correction_id: str | None = None


class AnalysisFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    turn_analysis_id: str | None = None
    correction_id: str | None = None
    rating: str
    reason: str | None = None
    created_at: datetime


class ConversationAnalysisSummaryRead(BaseModel):
    session_id: str
    session_analysis: SessionAnalysisRead | None = None
    turn_analyses: list[TurnAnalysisRead] = Field(default_factory=list)
    pending_jobs_count: int = 0
