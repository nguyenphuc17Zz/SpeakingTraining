"""Coach Core contracts (§6, §11, §22, §51-52)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class CoachMode(str, Enum):
    REFLEX = "reflex"          # Mode 1
    KEIGO = "keigo"            # Mode 2
    PITCH = "pitch"            # Mode 3
    SITUATIONAL = "situational" # Mode 4
    MONOLOGUE = "monologue"    # Mode 5
    FREE_SPEAKING = "free_speaking"
    REVIEW = "review"
    PROGRESS = "progress"
    DASHBOARD = "dashboard"
    LEARNING = "learning"
    SHADOWING = "shadowing"
    UNKNOWN = "unknown"


class CoachIntent(str, Enum):
    ASK = "ask"
    EXPLAIN = "explain"
    TEACH = "teach"
    RECOMMEND = "recommend"
    PRACTICE = "practice"
    ANALYZE = "analyze"
    REVIEW = "review"
    PLAN = "plan"
    MOTIVATE = "motivate"
    GENERAL = "general"


class CoachCapability(str, Enum):
    READ = "read"
    RECOMMEND = "recommend"
    GENERATE = "generate"
    EXECUTE = "execute"


class CoachResponseMode(str, Enum):
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"
    TEACHING = "teaching"


class MemoryType(str, Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    PREFERENCE = "preference"
    GOAL = "goal"
    HABIT = "habit"
    TREND = "trend"
    MASTERED_SKILL = "mastered_skill"
    PERSISTENT_ERROR = "persistent_error"


class InsightType(str, Enum):
    RETRIEVAL_BOTTLENECK = "retrieval_bottleneck"
    GRAMMAR_GAP = "grammar_gap"
    REGISTER_GAP = "register_gap"
    UCHI_SOTO_GAP = "uchi_soto_gap"
    PITCH_PATTERN_GAP = "pitch_pattern_gap"
    MORA_GAP = "mora_gap"
    FLUENCY_GAP = "fluency_gap"
    LEXICAL_REPETITION = "lexical_repetition"
    LOW_COHERENCE = "low_coherence"
    LOW_RECOVERY = "low_recovery"
    LOW_TASK_TRANSFER = "low_task_transfer"
    WEAK_AUTOMATICITY = "weak_automaticity"
    STRONG_PROGRESS = "strong_progress"
    STABLE_MASTERED_SKILL = "stable_mastered_skill"


# ── Evidence object §52 ──
class Evidence(BaseModel):
    metric: str
    value: float | int | str | None = None
    comparison: dict[str, Any] | None = None
    sample_count: int = 0
    comparable: bool = True
    source: str
    confidence: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


# ── CoachContext §6 ──
@dataclass
class CoachContext:
    user_id: str
    current_route: str  # e.g. /speaking, /reflex, /keigo
    current_mode: CoachMode
    current_sub_mode: str | None = None  # e.g. reflex_conjugation, keigo_transformation
    current_exercise_id: str | None = None
    current_session_id: str | None = None
    current_learning_targets: list[str] = field(default_factory=list)
    current_task: str | None = None
    current_scenario: str | None = None

    # learner state snapshots
    recent_attempts: list[dict[str, Any]] = field(default_factory=list)
    recent_errors: list[dict[str, Any]] = field(default_factory=list)
    mastery_snapshot: dict[str, Any] = field(default_factory=dict)
    automaticity_snapshot: dict[str, Any] = field(default_factory=dict)
    progress_summary: dict[str, Any] = field(default_factory=dict)
    active_recommendations: list[dict[str, Any]] = field(default_factory=list)

    learner_goals: list[str] = field(default_factory=list)
    learner_level: str = "N3"
    current_streak: int = 0

    # evidence-backed context hash for caching
    context_hash: str = ""
    # raw metrics for prompt
    metrics_summary: str = ""
    bottleneck_info: str = ""
    recent_weaknesses: str = ""
    recent_strengths: str = ""
    speaking_level: str = "Intermediate"
    level_confidence: str = "medium"
    total_sessions: int = 0

    # capability flags (what frontend can do)
    available_actions: list[str] = field(default_factory=list)
    capability_flags: dict[str, bool] = field(default_factory=dict)
    dashboard_overview: Any | None = None

    # detailed evidence (speaking)
    pronunciation_summary: dict[str, Any] = field(default_factory=dict)
    recent_corrections: list[dict[str, Any]] = field(default_factory=list)
    session_patterns: list[str] = field(default_factory=list)
    current_session_detail: dict[str, Any] | None = None


# ── Tool result §21 ──
class ToolResult(BaseModel):
    success: bool
    data: Any | None = None
    source: str
    confidence: float = 0.95
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── AI Output Schema §51 ──
class CoachNextAction(BaseModel):
    type: str  # START_SESSION, GENERATE_EXERCISE, NAVIGATE, etc.
    payload: dict[str, Any] = Field(default_factory=dict)
    label: str | None = None


class CoachAIOutput(BaseModel):
    response: str
    intent: str = CoachIntent.GENERAL.value
    confidence: float = 0.85
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    next_action: CoachNextAction | None = None
    key_points: list[str] = Field(default_factory=list)


# ── CoachResponse §43 ──
class CoachResponse(BaseModel):
    answer: str
    intent: str
    key_points: list[str] = Field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: str = "medium"
    next_action: dict[str, Any] | None = None
    is_deterministic: bool = False
    context_hash: str | None = None
    source: str = "coach_core"


# ── Micro-lesson §29 ──
class MicroLesson(BaseModel):
    problem: str
    why: str
    example: str
    try_prompt: str
    expected: str | None = None
    exercise_id: str | None = None


# ── Proactive trigger config §28 ──
class ProactiveThresholds(BaseModel):
    minimum_attempts: int = 5
    minimum_confidence: float = 0.80
    minimum_effect_size: float = 0.15
    cooldown_hours: int = 48
    insight_ttl_days: int = 7
