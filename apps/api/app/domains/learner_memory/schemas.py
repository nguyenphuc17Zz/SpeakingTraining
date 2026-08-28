from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class MemoryEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    memory_id: str
    session_id: str
    turn_id: str | None = None
    turn_analysis_id: str | None = None
    correction_id: str | None = None
    evidence_type: str
    weight: float
    original_snippet: str | None = None
    corrected_snippet: str | None = None
    context_tag: str | None = None
    created_at: datetime


class LearnerMemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    memory_type: str
    key: str
    statement: str
    category: str | None = None
    evidence_count: int
    confidence: float
    severity: str
    severity_score: int
    priority_score: float
    mastery: float
    attempt_count: int
    correct_count: int
    error_count: int
    first_seen: datetime
    last_seen: datetime
    trend: str
    status: str
    is_regression: bool
    contexts_used: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class LearnerMemoryDetailRead(LearnerMemoryRead):
    evidences: list[MemoryEvidenceRead] = Field(default_factory=list)


class LearnerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    overall_level: str
    speaking_level: str
    fluency_level: str
    grammar_level: str
    vocabulary_level: str
    naturalness_level: str
    confidence_score: float
    level_confidence: str
    total_sessions_analyzed: int
    total_turns_analyzed: int
    avg_response_speed_ms: float | None = None
    current_focus: str | None = None
    strengths: list[dict[str, Any]] | None = None
    weaknesses: list[dict[str, Any]] | None = None
    learning_goals: list[str] | None = None
    summary: str | None = None
    summary_version: int
    summary_generated_at: datetime | None = None
    last_recalculated_at: datetime


class MemoryFeedbackCreate(BaseModel):
    action: str = Field(description="'dismiss' | 'mark_inaccurate' | 'restore'")
    feedback_text: str | None = None


class MemoryFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    memory_id: str
    user_id: str
    action: str
    feedback_text: str | None = None
    created_at: datetime


class LearningPriorityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    type: str
    priority_score: float
    reason: str
    mastery: float
    trend: str
    recommended_focus: str
    evidence_count: int
    last_seen: datetime | None = None
