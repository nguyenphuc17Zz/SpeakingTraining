"""Monologue domain contracts — no hard-coded topic database, only conceptual ontology."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# --- Genre ontology (learning-system concepts, not language dataset) ---
class SpeechGenre(str, Enum):
    PERSONAL = "personal"
    STORY = "story"
    OPINION = "opinion"
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    ARGUMENT = "argument"
    PROBLEM_SOLUTION = "problem_solution"
    REFLECTION = "reflection"
    SUMMARY = "summary"
    REPORT = "report"
    INTERVIEW = "interview"
    BUSINESS_UPDATE = "business_update"
    PRESENTATION = "presentation"
    PERSUASION = "persuasion"
    CRITIQUE = "critique"
    PREDICTION = "prediction"


class SpeechSupportLevel(int, Enum):
    BLIND = 0          # Only topic
    KEYWORDS = 1       # 3-5 keywords
    GUIDED_QUESTIONS = 2  # What is your opinion? Why? Example?
    STRUCTURE = 3      # Introduction/Point/Reason/Example/Conclusion
    MINIMAL = 4        # No scaffolding, must organize independently


class SpeechDurationSec(int, Enum):
    S30 = 30
    S45 = 45
    S60 = 60
    S90 = 90
    S120 = 120
    S180 = 180
    S300 = 300


class SpeechPreparationSec(int, Enum):
    NONE = 0
    S15 = 15
    S30 = 30
    S60 = 60


class SpeechTopicDomain(str, Enum):
    DAILY_LIFE = "daily_life"
    EDUCATION = "education"
    WORK = "work"
    TECHNOLOGY = "technology"
    TRAVEL = "travel"
    RELATIONSHIPS = "relationships"
    CULTURE = "culture"
    FOOD = "food"
    HEALTH = "health"
    ENVIRONMENT = "environment"
    SOCIETY = "society"
    BUSINESS = "business"
    CAREER = "career"
    FUTURE = "future"
    PERSONAL_GROWTH = "personal_growth"
    HYPOTHETICAL = "hypothetical"
    CURRENT_ISSUES = "current_issues"


class SpeechSessionState(str, Enum):
    IDLE = "idle"
    PROMPTING = "prompting"
    PREPARING = "preparing"
    READY = "ready"
    RECORDING = "recording"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    RESULT = "result"
    RETRY = "retry"
    COMPLETED = "completed"


# Conceptual transition map for state machine
SPEECH_STATE_TRANSITIONS: dict[SpeechSessionState, list[SpeechSessionState]] = {
    SpeechSessionState.IDLE: [SpeechSessionState.PROMPTING],
    SpeechSessionState.PROMPTING: [SpeechSessionState.PREPARING, SpeechSessionState.READY],
    SpeechSessionState.PREPARING: [SpeechSessionState.READY, SpeechSessionState.RECORDING],
    SpeechSessionState.READY: [SpeechSessionState.RECORDING],
    SpeechSessionState.RECORDING: [SpeechSessionState.PROCESSING, SpeechSessionState.RETRY],
    SpeechSessionState.PROCESSING: [SpeechSessionState.ANALYZING, SpeechSessionState.RETRY],
    SpeechSessionState.ANALYZING: [SpeechSessionState.RESULT, SpeechSessionState.RETRY],
    SpeechSessionState.RESULT: [SpeechSessionState.COMPLETED, SpeechSessionState.RETRY, SpeechSessionState.IDLE],
    SpeechSessionState.RETRY: [SpeechSessionState.PREPARING, SpeechSessionState.READY, SpeechSessionState.IDLE],
    SpeechSessionState.COMPLETED: [SpeechSessionState.IDLE],
}


# --- Pydantic DTOs ---

class SpeechSupport(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    outline: list[str] = Field(default_factory=list)
    guided_questions: list[str] = Field(default_factory=list)


class SpeechTaskSpec(BaseModel):
    topic: str
    instruction: str  # Japanese (VI+JP hybrid: topic VI, instruction JP)
    genre: SpeechGenre
    topic_domain: SpeechTopicDomain
    difficulty: int = Field(ge=1, le=5)
    expected_duration_sec: int
    prep_duration_sec: int
    support_level: SpeechSupportLevel
    support: SpeechSupport = Field(default_factory=SpeechSupport)
    constraints: list[str] = Field(default_factory=list)
    learning_targets: list[str] = Field(default_factory=list)
    outline_hint: list[str] = Field(default_factory=list)
    session_signature: str | None = None
    provider: str | None = None
    model: str | None = None


class SpeechGenerationInput(BaseModel):
    user_id: str
    overall_level: str = "N3"
    speaking_level: str = "N3"
    recent_signatures: list[str] = Field(default_factory=list)
    recent_topics: list[str] = Field(default_factory=list)
    recent_genres: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    career_domain: str | None = None
    learning_targets: list[str] = Field(default_factory=list)
    weaknesses: list[dict[str, Any]] = Field(default_factory=list)
    difficulty: int | None = None
    duration_sec: int = 60
    prep_sec: int = 30
    genre: str | None = None
    support_level: int | None = None
    # optional overrides
    topic_domain: str | None = None
    seed: str | None = None


class PauseClass(str, Enum):
    MICRO_PAUSE = "micro_pause"       # <0.5s
    NORMAL_PAUSE = "normal_pause"     # 0.5-1.0
    LONG_PAUSE = "long_pause"         # 1.0-1.5
    STALL = "stall"                   # 1.5-3.0
    BREAKDOWN = "breakdown"           # >3.0


class PauseContext(str, Enum):
    SENTENCE_BOUNDARY = "sentence_boundary"
    CLAUSE_BOUNDARY = "clause_boundary"
    BEFORE_NEW_IDEA = "before_new_idea"
    INSIDE_PHRASE = "inside_phrase"
    BEFORE_PREDICATE = "before_predicate"
    AFTER_FILLER = "after_filler"
    AFTER_SELF_REPAIR = "after_self_repair"
    UNKNOWN = "unknown"


class TokenClass(str, Enum):
    FILLER = "filler"
    DISCOURSE_MARKER = "discourse_marker"
    BACKCHANNEL = "backchannel"
    CONTENT_WORD = "content_word"
    SELF_REPAIR = "self_repair"


class ConnectorClass(str, Enum):
    SEQUENCE = "sequence"
    ADDITION = "addition"
    CONTRAST = "contrast"
    CAUSE = "cause"
    EFFECT = "effect"
    EXAMPLE = "example"
    CLARIFICATION = "clarification"
    EMPHASIS = "emphasis"
    SUMMARY = "summary"
    CONCLUSION = "conclusion"


# Analytics result fragments

class PauseEvent(BaseModel):
    start_ms: int
    end_ms: int
    duration_ms: int
    pause_class: PauseClass
    context: PauseContext = PauseContext.UNKNOWN


class FillerEvent(BaseModel):
    token: str
    start_ms: int | None = None
    end_ms: int | None = None
    token_class: TokenClass = TokenClass.FILLER


class SelfRepairEvent(BaseModel):
    type: str  # restart|reformulation|correction|abandoned_clause|clarification|lexical_replacement
    fragment: str
    start_ms: int | None = None
    success: bool = True


class SpeechMetrics(BaseModel):
    # deterministic authoritative counts
    speech_duration_ms: int
    target_duration_ms: int
    total_chars: int
    total_tokens: int
    mora_count: int | None = None
    chars_per_min: float
    tokens_per_min: float
    mora_per_sec: float | None = None
    speech_seconds_per_min: float | None = None
    pause_count: int
    pause_events: list[PauseEvent] = Field(default_factory=list)
    filler_count: int
    filler_events: list[FillerEvent] = Field(default_factory=list)
    filler_per_min: float
    filler_ratio: float
    long_pause_count: int
    stall_count: int
    breakdown_count: int
    self_repair_count: int
    self_repair_events: list[SelfRepairEvent] = Field(default_factory=list)
    abandoned_rate: float = 0.0
    stt_confidence: float | None = None
    audio_quality: str | None = None
    word_count: int = 0


class IdeaDensityResult(BaseModel):
    unique_ideas: int
    supporting_details: int
    examples: int
    repeated_ideas: int
    idea_density_score: float


class LexicalProfile(BaseModel):
    unique_lemmas: int
    type_token_ratio: float
    mattr: float
    content_word_variety: float
    repetition_clusters: list[dict[str, Any]] = Field(default_factory=list)
    frequency_profile: dict[str, int] = Field(default_factory=dict)  # basic/intermediate/advanced/specialized
    jlpt_approx: dict[str, int] = Field(default_factory=dict)


class DiscourseMapResult(BaseModel):
    detected_structure: list[str] = Field(default_factory=list)  # Opening, Opinion, Reason...
    expected_structure: list[str] = Field(default_factory=list)
    missing_elements: list[str] = Field(default_factory=list)
    connector_counts: dict[str, int] = Field(default_factory=dict)
    connector_quality: str = "unknown"  # present|appropriate|repeated|misused|missing


class CoherenceScore(BaseModel):
    idea_progression: float = Field(ge=0, le=100)
    logical_linkage: float = Field(ge=0, le=100)
    reference_clarity: float = Field(ge=0, le=100)
    topic_continuity: float = Field(ge=0, le=100)
    conclusion_quality: float = Field(ge=0, le=100)
    overall: float = Field(ge=0, le=100)


class SpeechQualityGateResult(BaseModel):
    status: str  # ok|LOW_CONFIDENCE|RETRY_AUDIO
    reason: str | None = None
    audio_confidence: float | None = None
    stt_confidence: float | None = None
    clipping: bool = False
    has_voice: bool = True


class SpeechAIResult(BaseModel):
    relevance: float = Field(ge=0, le=100)
    coherence: float = Field(ge=0, le=100)
    naturalness: float = Field(ge=0, le=100)
    genre_fit: float = Field(ge=0, le=100)
    argument_quality: float | None = None
    content_score: float | None = None
    main_strength: str | None = None
    main_weakness: str | None = None
    feedback: list[str] = Field(default_factory=list)
    upgrade: dict[str, Any] | None = None  # {minimal_correction, native_version, professional_version}
    confidence: float = Field(ge=0, le=1, default=0.85)


class SpeechAssessment(BaseModel):
    overall: float = Field(ge=0, le=100)
    fluency: float = Field(ge=0, le=100)
    coherence: float = Field(ge=0, le=100)
    grammar: float = Field(ge=0, le=100)
    vocabulary: float = Field(ge=0, le=100)
    naturalness: float = Field(ge=0, le=100)
    relevance: float = Field(ge=0, le=100)
    discourse: float = Field(ge=0, le=100)
    pronunciation: float = Field(ge=0, le=100)
    content: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1, default=0.85)
    weights_used: dict[str, float] = Field(default_factory=dict)
    genre: str | None = None
    # timelines / maps
    fluency_timeline: list[dict[str, Any]] = Field(default_factory=list)
    filler_timeline: list[dict[str, Any]] = Field(default_factory=list)
    discourse_map: DiscourseMapResult | None = None
    idea_map: IdeaDensityResult | None = None
    lexical_profile: LexicalProfile | None = None
    speech_metrics: SpeechMetrics | None = None
    quality_gate: SpeechQualityGateResult | None = None
    ai_result: SpeechAIResult | None = None
    upgrade_explanations: list[dict[str, str]] = Field(default_factory=list)
