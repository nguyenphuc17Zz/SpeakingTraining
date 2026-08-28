from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class LearningGoalType(str, Enum):
    SPEAKING = "speaking"
    PRONUNCIATION = "pronunciation"
    CONVERSATION = "conversation"
    WORKPLACE = "workplace"
    TRAVEL = "travel"
    INTERVIEW = "interview"
    JLPT = "jlpt"
    NATURALNESS = "naturalness"
    FLUENCY = "fluency"


class LearningGoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class LearningItemType(str, Enum):
    GRAMMAR = "grammar"
    PARTICLE = "particle"
    CONJUGATION = "conjugation"
    VOCABULARY = "vocabulary"
    WORD_CHOICE = "word_choice"
    NATURALNESS = "naturalness"
    POLITENESS = "politeness"
    FILLER = "filler"
    FLUENCY = "fluency"
    PRONUNCIATION = "pronunciation"
    PITCH_ACCENT = "pitch_accent"
    SENTENCE_PATTERN = "sentence_pattern"


class LearningItemLifecycle(str, Enum):
    DISCOVERED = "discovered"
    ACTIVE = "active"
    PRACTICING = "practicing"
    IMPROVING = "improving"
    MASTERED = "mastered"
    MAINTENANCE = "maintenance"
    REGRESSED = "regressed"


class LearningItemStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DISMISSED = "dismissed"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    CHALLENGE = "challenge"


class ScaffoldingLevel(str, Enum):
    NONE = "none"
    KEYWORD_HINT = "keyword_hint"
    SENTENCE_STARTER = "sentence_starter"
    STRUCTURED_OPTIONS = "structured_options"
    FULL_EXAMPLE = "full_example"


class ExerciseType(str, Enum):
    CONVERSATION = "conversation"
    ROLEPLAY = "roleplay"
    RAPID_RESPONSE = "rapid_response"
    SENTENCE_GENERATION = "sentence_generation"
    SENTENCE_TRANSFORMATION = "sentence_transformation"
    TRANSLATION_SPEAKING = "translation_speaking"
    PRONUNCIATION_REPEAT = "pronunciation_repeat"
    SHADOWING = "shadowing"
    CORRECTION_RETRY = "correction_retry"
    STORYTELLING = "storytelling"
    OPINION = "opinion"
    QUESTION_ANSWER = "question_answer"
    SCENARIO = "scenario"
    REFLEX_CONJUGATION = "reflex_conjugation"
    REFLEX_QNA = "reflex_qna"
    REFLEX_TRANSFORMATION = "reflex_transformation"
    REFLEX_CONTEXT = "reflex_context"
    KEIGO_SONKEIGO = "keigo_sonkeigo"
    KEIGO_KENJOUGO = "keigo_kenjougo"
    KEIGO_TEINEIGO = "keigo_teineigo"
    KEIGO_TRANSFORMATION = "keigo_transformation"
    KEIGO_CONTEXT = "keigo_context"
    KEIGO_DOCTOR = "keigo_doctor"
    KEIGO_NATURALNESS = "keigo_naturalness"
    PITCH_MINIMAL_PAIR = "pitch_minimal_pair"
    PITCH_MORA_LENGTH = "mora_length"
    PITCH_VOWEL_DEVOICING = "vowel_devoicing"
    PITCH_CONTOUR = "pitch_contour"
    PITCH_RECOGNITION = "pitch_recognition"
    SITUATIONAL_ROLEPLAY = "situational_roleplay"
    SITUATIONAL_SCENARIO = "situational_scenario"
    SPEECH_MONOLOGUE = "speech_monologue"


class ExerciseStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


class IndependenceLevel(str, Enum):
    INDEPENDENT = "independent"      # No hints, completely spontaneous
    ASSISTED_HINT = "assisted_hint"  # Used keyword hint or sentence starter
    RETRY_SUCCESS = "retry_success"  # Succeeded after guided retry
    SCAFFOLDED = "scaffolded"        # Read full example or heavy scaffold


class MasteryDimension(BaseModel):
    recognition: float = Field(default=0.0, ge=0.0, le=1.0)
    production: float = Field(default=0.0, ge=0.0, le=1.0)
    spontaneous_production: float = Field(default=0.0, ge=0.0, le=1.0)
    context_variety: float = Field(default=0.0, ge=0.0, le=1.0)


class PriorityScore(BaseModel):
    key: str
    item_type: LearningItemType
    title: str
    priority_score: float = Field(ge=0.0, le=1.0)
    reason: str
    goal_relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    recommended_exercise_type: ExerciseType = ExerciseType.ROLEPLAY
    estimated_minutes: int = 5
    difficulty: DifficultyLevel = DifficultyLevel.NORMAL
    weakness_factor: float = 0.5
    recurrence_factor: float = 0.5
    recency_factor: float = 1.0
    mastery_gap: float = 0.5
    learning_value: float = 0.8
    uncertainty_boost: float = 0.0
    regression_boost: float = 0.0


class LearnerLearningState(BaseModel):
    user_id: str
    overall_level: str
    speaking_level: str
    confidence_score: float
    level_confidence: str
    active_goals: list[str] = Field(default_factory=list)
    top_weaknesses: list[dict[str, Any]] = Field(default_factory=list)
    top_strengths: list[dict[str, Any]] = Field(default_factory=list)
    active_learning_items: list[dict[str, Any]] = Field(default_factory=list)
    review_due_items: list[dict[str, Any]] = Field(default_factory=list)
    pronunciation_priorities: list[dict[str, Any]] = Field(default_factory=list)
    grammar_priorities: list[dict[str, Any]] = Field(default_factory=list)
    fluency_priorities: list[dict[str, Any]] = Field(default_factory=list)
    naturalness_priorities: list[dict[str, Any]] = Field(default_factory=list)
    recent_performance: dict[str, Any] = Field(default_factory=dict)
    mastery_distribution: dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExerciseSpec(BaseModel):
    id: str | None = None
    type: ExerciseType
    title: str
    objective: str
    scenario: str | None = None
    instructions: str
    constraints: list[str] = Field(default_factory=list)
    target_patterns: list[str] = Field(default_factory=list)
    expected_behavior: str | None = None
    difficulty: DifficultyLevel = DifficultyLevel.NORMAL
    scaffold_level: ScaffoldingLevel = ScaffoldingLevel.NONE
    scaffold_hint: str | None = None
    estimated_minutes: int = 5
    learning_item_keys: list[str] = Field(default_factory=list)
    persona_role: str | None = None
    persona_difficulty: str | None = "N3"
    acceptable_variants: list[str] = Field(default_factory=list)


class ExerciseResult(BaseModel):
    exercise_id: str
    user_id: str
    score: float = Field(ge=0.0, le=100.0)
    success: bool
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    target_mastery_delta: dict[str, float] = Field(default_factory=dict)
    feedback: str
    evidence: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    independence: IndependenceLevel = IndependenceLevel.INDEPENDENT
    response_speed_ms: float | None = None
    target_usage: str = "correct"  # correct | incorrect | partial | not_attempted
    pronunciation_score: float | None = None
    grammar_score: float | None = None
    naturalness_score: float | None = None
    attempt_id: str | None = None


class ReviewDecision(BaseModel):
    learning_item_key: str
    next_review_at: datetime
    interval_days: int
    review_streak: int
    reason: str
    new_lifecycle: LearningItemLifecycle


class CurriculumUnit(BaseModel):
    id: str
    title: str
    objective: str
    target_learning_items: list[str] = Field(default_factory=list)
    recommended_exercise_types: list[ExerciseType] = Field(default_factory=list)
    completion_criteria: str
    estimated_sessions: int = 3
    is_completed: bool = False
    progress_ratio: float = 0.0
