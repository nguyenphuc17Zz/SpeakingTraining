"""Reflex domain contracts — DTOs for 4 sub-modes, assessments, and adaptive pressure."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReflexSubMode(str, Enum):
    CONJUGATION = "reflex_conjugation"
    QNA = "reflex_qna"
    TRANSFORMATION = "reflex_transformation"
    CONTEXT = "reflex_context"
    VOCABULARY = "reflex_vocabulary"
    KEIGO_VOCABULARY = "reflex_keigo_vocab"


class ConjugationFormDTO(BaseModel):
    verb: str = Field(description="Dictionary form, e.g. 書く")
    target: str = Field(description="Target label: 使役受身・過去 or te etc")
    timer_limit_ms: int = 3000


class SpeedQnARequestDTO(BaseModel):
    question: str
    expected_length: str = "short"  # short | medium | long
    topic: str | None = None


class TransformationTaskDTO(BaseModel):
    source_sentence: str
    task: str = Field(description="e.g. カジュアルな過去形にしてください。")
    target_register: str | None = None  # casual | polite | past | negative etc


class ContextualReactionDTO(BaseModel):
    scenario: str
    relationship: str = "casual"
    intent: str
    constraint: str | None = None
    target_feature: str | None = None


class ReflexExerciseGenerateRequest(BaseModel):
    sub_mode: ReflexSubMode
    pressure_level: str = "normal"  # relaxed | normal | fast | reflex | extreme
    timer_limit_ms: int | None = None  # overrides pressure if set
    difficulty: str | None = None  # easy | normal | hard | challenge
    learning_item_key: str | None = None
    verb: str | None = None  # for conjugation
    conjugation_target: str | None = None
    source_sentence: str | None = None  # for transformation
    scenario_intent: str | None = None
    subtitle_mode: str | None = None  # hidden | japanese | japanese_reading | vietnamese
    prompt_mode: str | None = None  # ja_audio | ja_text | vi_situation | image | ja_qna


class ReflexExerciseDTO(BaseModel):
    id: str
    sub_mode: str
    title: str
    prompt: str
    prompt_reading: str | None = None
    prompt_translation: str | None = None
    scenario: str | None = None
    instructions: str
    timer_limit_ms: int
    pressure_level: str
    difficulty: str
    acceptable_variants: list[str] = Field(default_factory=list)
    canonical: str | None = None
    semantic_target: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ReflexAttemptRequest(BaseModel):
    exercise_id: str
    user_transcript: str = ""
    raw_transcript: str | None = None
    # Timing from frontend (performance.now deltas)
    prompt_completed_at: str | None = None  # ISO or ms epoch as string
    speech_started_at: str | None = None
    speech_ended_at: str | None = None
    reaction_latency_ms: float | None = None
    semantic_latency_ms: float | None = None
    response_duration_ms: float | None = None
    timer_limit_ms: int | None = None
    timed_out: bool = False
    late_response: bool = False
    interrupted_prompt: bool = False
    speech_confidence: float | None = None
    independence: str = "independent"  # independent | with_hint | with_example | with_translation
    used_hint: bool = False
    subtitle_mode: str | None = None


class DimensionDTO(BaseModel):
    score: float
    confidence: float
    evidence: list[str] = Field(default_factory=list)


class ReflexAssessmentDTO(BaseModel):
    reaction: DimensionDTO
    accuracy: DimensionDTO
    naturalness: DimensionDTO
    fluency: DimensionDTO
    context_fit: DimensionDTO
    independence: DimensionDTO
    completeness: DimensionDTO
    overall: DimensionDTO
    timed_out: bool = False
    late_response: bool = False
    reaction_latency_ms: float | None = None
    semantic_latency_ms: float | None = None
    timer_limit_ms: int | None = None


class ReflexAttemptResultDTO(BaseModel):
    attempt_id: str
    exercise_id: str
    success: bool
    is_perfect: bool = False
    is_personal_best: bool = False
    timed_out: bool = False
    late_response: bool = False
    transcript: str
    normalized_transcript: str | None = None
    assessment: ReflexAssessmentDTO
    feedback: str
    expected: dict[str, Any] | None = None
    mastery_deltas: dict[str, float] = Field(default_factory=dict)
    xp_awarded: int | None = None


class ReflexProgressDTO(BaseModel):
    user_id: str
    period: str = "30d"
    total_attempts: int = 0
    accuracy_rate: float = 0.0
    avg_reaction_ms: float | None = None
    p50_reaction_ms: float | None = None
    p90_reaction_ms: float | None = None
    timeout_rate: float = 0.0
    automaticity_avg: float | None = None
    pressure_threshold_ms: int | None = None
    comfort_window: str | None = None  # e.g. "2.4–3.0s"
    by_sub_mode: dict[str, Any] = Field(default_factory=dict)


class ReflexSessionCreateRequest(BaseModel):
    sub_modes: list[str] | None = None  # default mixed
    pressure_level: str = "normal"
    duration_minutes: int = Field(default=5, ge=1, le=30)
    exercise_count: int | None = None  # overrides duration if set
    focus: str | None = None  # grammar_automaticity | response_speed | naturalness | workplace | casual | mixed
    mixed: bool = True


class ReflexSessionDTO(BaseModel):
    id: str
    user_id: str
    status: str = "active"
    sub_modes: list[str]
    pressure_level: str
    timer_limit_ms: int
    duration_minutes: int
    exercises: list[ReflexExerciseDTO] = Field(default_factory=list)
    created_at: datetime
