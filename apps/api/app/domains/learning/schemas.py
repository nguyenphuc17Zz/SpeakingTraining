from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# Goals
class LearningGoalCreate(BaseModel):
    title: str
    goal_type: str = "speaking"
    description: str | None = None
    priority: int = 1
    target_date: datetime | None = None


class LearningGoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    target_date: datetime | None = None


class LearningGoalDTO(BaseModel):
    id: str
    title: str
    description: str | None
    goal_type: str
    priority: int
    status: str
    target_date: datetime | None
    created_at: datetime
    updated_at: datetime


# Learning Items
class LearningItemDTO(BaseModel):
    id: str
    key: str
    item_type: str
    title: str
    description: str | None
    difficulty: str
    lifecycle: str
    status: str
    overall_mastery: float
    recognition_mastery: float
    production_mastery: float
    spontaneous_mastery: float
    context_variety_score: float
    automaticity_mastery: float = 0.0
    confidence: float
    priority_score: float
    attempt_count: int
    success_count: int
    review_streak: int
    review_interval_days: int
    last_practiced_at: datetime | None
    next_review_at: datetime | None


# Exercises
class ExerciseDTO(BaseModel):
    id: str
    exercise_type: str
    status: str
    title: str
    objective: str
    scenario: str | None
    instructions: str
    constraints: list[str] = Field(default_factory=list)
    target_patterns: list[str] = Field(default_factory=list)
    difficulty: str
    scaffold_level: str
    scaffold_hint: str | None
    estimated_minutes: int
    created_at: datetime
    extra_metadata: dict[str, Any] | None = None
    acceptable_variants: list[str] | None = None


class ExerciseGenerateRequest(BaseModel):
    learning_item_key: str | None = None
    exercise_type: str | None = None
    difficulty: str | None = None


class ExerciseStartRequest(BaseModel):
    session_id: str | None = None
    pronunciation_attempt_id: str | None = None


class ExerciseStartResponse(BaseModel):
    attempt_id: str
    exercise_id: str
    status: str
    started_at: datetime


class ReflexMetrics(BaseModel):
    """Reflex-specific timing metrics captured from audio timestamps (not STT completion)."""

    reaction_latency_ms: float | None = None
    semantic_latency_ms: float | None = None
    response_duration_ms: float | None = None
    timer_limit_ms: int | None = None
    timed_out: bool = False
    late_response: bool = False
    interrupted_prompt: bool = False
    speech_confidence: float | None = None
    thinking_stall_ms: float | None = None
    pressure_level: str | None = None
    independence: str | None = None


KeigoMetrics = ReflexMetrics  # alias for keigo (same timing fields)
PitchMetrics = ReflexMetrics  # alias for pitch (same timing + pitch_confidence)
SituationalMetrics = ReflexMetrics  # alias for situational (same timing + intent)
SpeechMetrics = ReflexMetrics  # alias for speech monologue (same timing + speech_duration)


class ExerciseSubmitRequest(BaseModel):
    user_transcript: str = ""
    turn_analysis_score: float | None = None
    pronunciation_score: float | None = None
    response_speed_ms: float | None = None
    used_hint: bool = False
    plan_item_id: str | None = None
    reflex_metrics: ReflexMetrics | None = None
    keigo_metrics: ReflexMetrics | None = None
    pitch_metrics: ReflexMetrics | None = None
    situational_metrics: ReflexMetrics | None = None
    speech_metrics: SpeechMetrics | None = None
    # Raw audio for server-side STT (monologue authoritative)
    audio_base64: str | None = None
    speech_duration_ms: int | None = None
    target_duration_ms: int | None = None
    # Legacy direct reflex/keigo/pitch/situational fields (flattened for frontend convenience)
    reaction_latency_ms: float | None = None
    semantic_latency_ms: float | None = None
    timer_limit_ms: int | None = None
    timed_out: bool | None = None
    late_response: bool | None = None
    speech_confidence: float | None = None
    pitch_confidence: float | None = None
    audio_quality: float | None = None


class ExerciseResultDTO(BaseModel):
    exercise_id: str
    score: float
    success: bool
    confidence: float
    target_mastery_delta: dict[str, float]
    feedback: str
    evidence: list[str]
    metrics: dict[str, Any]
    independence: str
    response_speed_ms: float | None
    target_usage: str | None


# Daily Plan
class LearningPlanItemDTO(BaseModel):
    id: str
    plan_id: str
    exercise_id: str
    order_index: int
    target_type: str
    title: str
    estimated_minutes: int
    status: str
    completed_at: datetime | None
    exercise: ExerciseDTO | None = None


class DailyPlanDTO(BaseModel):
    id: str
    plan_date: str
    time_budget_minutes: int
    status: str
    focus_title: str
    focus_reason: str | None
    generator_version: str
    generated_at: datetime
    items: list[LearningPlanItemDTO]


class DailyPlanRegenerateRequest(BaseModel):
    time_budget_minutes: int = 30


# Recommendations & Priorities
class LearningRecommendationDTO(BaseModel):
    key: str
    item_type: str
    title: str
    priority_score: float
    why: str
    how: str
    recommended_exercise_type: str
    estimated_minutes: int
    difficulty: str
    mastery_percent: int
    attempt_count: int
    success_count: int
    goal_relevance: float


class CurriculumUnitDTO(BaseModel):
    id: str
    title: str
    objective: str
    target_learning_items: list[str]
    recommended_exercise_types: list[str]
    completion_criteria: str
    estimated_sessions: int
    is_completed: bool
    progress_ratio: float
