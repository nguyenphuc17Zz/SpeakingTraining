from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CorrectionCategory(str, Enum):
    GRAMMAR = "grammar"
    WORD_CHOICE = "word_choice"
    PARTICLE = "particle"
    CONJUGATION = "conjugation"
    NATURALNESS = "naturalness"
    POLITENESS = "politeness"
    CONTEXT = "context"
    PRONUNCIATION_PLACEHOLDER = "pronunciation_placeholder"


class CorrectionSeverity(str, Enum):
    MUST_FIX = "MUST_FIX"
    SHOULD_FIX = "SHOULD_FIX"
    NATIVE_ALTERNATIVE = "NATIVE_ALTERNATIVE"
    IGNORE = "IGNORE"


class AnalysisConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FeedbackRating(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    WRONG_CORRECTION = "wrong_correction"


class CorrectionItem(BaseModel):
    id: str | None = None
    category: CorrectionCategory
    severity: CorrectionSeverity
    original: str = Field(description="The user's original snippet or phrase that triggered this item.")
    corrected: str = Field(description="The recommended correct or natural replacement.")
    explanation: str = Field(description="Concise, respectful explanation in Vietnamese.")
    native_alternative: str | None = Field(default=None, description="Native colloquial or situational alternative.")
    acceptable_alternatives: list[str] = Field(default_factory=list, description="Other grammatically valid variations.")
    context_note: str | None = Field(default=None, description="Contextual explanation (e.g. casual vs polite).")
    confidence: AnalysisConfidence = AnalysisConfidence.HIGH
    severity_score: int = Field(default=50, ge=0, le=100, description="Internal severity score for ranking.")


class GrammarPointNote(BaseModel):
    id: str | None = None
    grammar_pattern: str = Field(description="Identified grammar pattern (e.g. 〜わけではない, 〜てしまう).")
    user_usage: str = Field(description="How the learner used the structure.")
    correct_usage: str = Field(description="Standard grammatical usage.")
    short_explanation: str = Field(description="Short pedagogical explanation in Vietnamese.")
    example_sentence: str | None = Field(default=None, description="Natural Japanese example sentence.")


class VocabularyNote(BaseModel):
    id: str | None = None
    original_word: str = Field(description="Word or expression used by user.")
    suggested_alternatives: list[str] = Field(default_factory=list, description="Better or richer vocabulary options.")
    nuance_explanation: str = Field(description="Explanation of nuances in Vietnamese.")
    jlpt_level: str | None = Field(default=None, description="Estimated JLPT level e.g. N3, N2.")


class ContextNote(BaseModel):
    persona_role: str | None = None
    formality_level: str = Field(default="appropriate", description="appropriate | too_casual | too_formal | mismatched")
    observation: str = Field(description="Observation regarding persona relationship and situational context.")


class TurnAnalysisResult(BaseModel):
    turn_id: str
    session_id: str
    overall_quality_score: int = Field(default=80, ge=0, le=100)
    communicative_success: bool = Field(default=True)
    corrections: list[CorrectionItem] = Field(default_factory=list)
    grammar_points: list[GrammarPointNote] = Field(default_factory=list)
    vocabulary_notes: list[VocabularyNote] = Field(default_factory=list)
    context_notes: list[ContextNote] = Field(default_factory=list)
    priority_issues: list[CorrectionItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list, description="Mandatory positive reinforcement at turn level.")
    is_suspicious_transcript: bool = Field(default=False, description="Flagged if STT confidence was poor.")
    prompt_version: str = "conversation.analysis.v1"
    analyzer_version: str = "1.0.0"
    provider: str | None = None
    model: str | None = None
    analyzed_at: datetime | None = None


class SessionAnalysisResult(BaseModel):
    session_id: str
    overall_score: int = Field(default=75, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list, description="Mandatory positive reinforcement observations.")
    weaknesses: list[str] = Field(default_factory=list, description="Areas needing improvement.")
    repeated_issues: list[dict[str, Any]] = Field(default_factory=list, description="Mistakes or patterns appearing multiple times.")
    top_recommendations: list[str] = Field(default_factory=list, max_length=5, description="Top actionable recommendations.")
    total_user_turns_analyzed: int = 0
    total_corrections_count: int = 0
    must_fix_count: int = 0
    should_fix_count: int = 0
    native_alt_count: int = 0
    grammar_summary: list[str] = Field(default_factory=list)
    vocabulary_summary: list[str] = Field(default_factory=list)
    prompt_version: str = "session.analysis.v1"
    analyzer_version: str = "1.0.0"
    provider: str | None = None
    model: str | None = None
    analyzed_at: datetime | None = None


class ConversationAnalysisInput(BaseModel):
    session_id: str
    current_turn_id: str
    current_user_transcript: str
    stt_confidence: float | None = None
    speech_duration_ms: int | None = None
    conversation_mode: str = "conversation"  # 'conversation' | 'coaching'
    persona_name: str = "Assistant"
    persona_role: str = "Conversational Partner"
    persona_difficulty: str = "N3"
    persona_style: str = "Polite and natural"
    learner_level: str = "N3"
    previous_turns: list[dict[str, Any]] = Field(default_factory=list)


class AnalysisPolicyConfig(BaseModel):
    max_corrections_per_turn: int = 3
    skip_trivial_threshold_chars: int = 4
    enable_turn_analysis: bool = True
    enable_session_analysis: bool = True
    feedback_style: str = "balanced"  # 'minimal' | 'balanced' | 'deep'
    explanation_language: str = "vi"  # 'vi' | 'ja' | 'en'
