from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    GRAMMAR = "grammar"
    PARTICLE = "particle"
    CONJUGATION = "conjugation"
    VOCABULARY = "vocabulary"
    WORD_CHOICE = "word_choice"
    NATURALNESS = "naturalness"
    POLITENESS = "politeness"
    FILLER = "filler"
    FLUENCY = "fluency"
    SENTENCE_PATTERN = "sentence_pattern"
    SPEAKING_HABIT = "speaking_habit"
    STRENGTH = "strength"
    PREFERENCE = "preference"
    GOAL = "goal"
    PRONUNCIATION = "pronunciation"
    PITCH_ACCENT = "pitch_accent"
    PRONUNCIATION_PLACEHOLDER = "pronunciation_placeholder"


class MemoryStatus(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    IMPROVING = "improving"
    STABLE = "stable"
    RESOLVED = "resolved"
    ARCHIVED = "archived"
    DISMISSED = "dismissed"


class MemoryTrend(str, Enum):
    NEW = "new"
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"


class LearnerLevel(str, Enum):
    BEGINNER = "beginner"            # JLPT N5 equivalent
    ELEMENTARY = "elementary"        # JLPT N4 equivalent
    INTERMEDIATE = "intermediate"    # JLPT N3 equivalent
    UPPER_INTERMEDIATE = "upper_intermediate"  # JLPT N2 equivalent
    ADVANCED = "advanced"            # JLPT N1 equivalent


class LevelConfidence(str, Enum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MemoryCandidate(BaseModel):
    """Candidate memory extracted from turn-by-turn analysis or session review."""
    memory_type: MemoryType
    key: str = Field(description="Canonical stable identifier e.g. particle.ha_vs_ga, filler.nanka")
    statement: str = Field(description="Human-readable description in Vietnamese/English.")
    category: str = Field(default="general")
    severity: str = "SHOULD_FIX"  # MUST_FIX, SHOULD_FIX, NATIVE_ALTERNATIVE, STRENGTH, GOAL
    severity_score: int = 50
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence_weight: float = Field(default=1.0, ge=0.0, le=2.0)
    evidence_type: str = "error_observation"  # error_observation | correct_observation | session_pattern | strength | goal
    original_snippet: str | None = None
    corrected_snippet: str | None = None
    context_tag: str | None = None
    session_id: str
    turn_id: str | None = None
    turn_analysis_id: str | None = None
    correction_id: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LearningPriority(BaseModel):
    """Priority recommendation object for adaptive curriculum & practice (Phase 7 contract)."""
    key: str
    type: MemoryType
    priority_score: float = Field(ge=0.0, le=1.0)
    reason: str
    mastery: float = Field(ge=0.0, le=1.0)
    trend: MemoryTrend
    recommended_focus: str
    evidence_count: int = 0
    last_seen: datetime | None = None


class LearnerContextBudget(BaseModel):
    """Compact context DTO for AI prompt injection."""
    level: str
    level_confidence: str
    current_goals: list[str] = Field(default_factory=list)
    priority_weaknesses: list[str] = Field(default_factory=list)
    speaking_strengths: list[str] = Field(default_factory=list)
    current_focus: str | None = None
    compact_prompt_block: str = ""


class LearnerSummaryDTO(BaseModel):
    overall_level: str
    speaking_level: str
    fluency_level: str
    grammar_level: str
    vocabulary_level: str
    naturalness_level: str
    confidence_score: float
    level_confidence: str
    total_sessions: int
    total_turns: int
    top_strengths: list[dict[str, Any]]
    top_weaknesses: list[dict[str, Any]]
    goals: list[str]
    ai_summary: str | None
    last_recalculated_at: datetime
