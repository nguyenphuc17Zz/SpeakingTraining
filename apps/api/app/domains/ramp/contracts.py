"""Mode 6 Speaking Ramp — core contracts, enums, and Pydantic models.

§3 Core Training Model, §5 Support Levels, §6 Exercise Types,
§34 RampScore, §67 Session State, §22 Response Length Target.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Stage ontology (§3)
# ---------------------------------------------------------------------------

class RampStage(int, Enum):
    """0–10 speaking ramp stages. 11 = ready for Mode 5."""
    ECHO = 0                   # Repetition warm-up
    SUBSTITUTE = 1             # Controlled substitution
    COMPLETE = 2               # Sentence completion
    ONE_SENTENCE = 3           # One-sentence response
    EXPAND = 4                 # Two-sentence expansion
    REASON = 5                 # Answer + reason
    EXAMPLE = 6                # Answer + reason + example
    MULTI_IDEA = 7             # Multi-idea response
    SPONTANEOUS_SHORT = 8      # 20–30s spontaneous
    SPONTANEOUS_MID = 9        # 30–45s spontaneous
    SPONTANEOUS_LONG = 10      # 45–60s independent
    # 11+ → Mode 5 territory


STAGE_TARGET_DURATION_SEC: dict[int, int] = {
    0: 0,    # echo: no duration target
    1: 0,
    2: 0,
    3: 5,
    4: 10,
    5: 15,
    6: 20,
    7: 25,
    8: 25,
    9: 35,
    10: 50,
}

STAGE_MIN_ATTEMPTS_BEFORE_CHANGE = 5  # §31 evidence-based progression


# ---------------------------------------------------------------------------
# Exercise types (§6)
# ---------------------------------------------------------------------------

class RampExerciseType(str, Enum):
    SPEAK_ECHO = "speak_echo"
    SPEAK_SUBSTITUTE = "speak_substitute"
    SPEAK_COMPLETE = "speak_complete"
    SPEAK_ONE_SENTENCE = "speak_one_sentence"
    SPEAK_EXPAND = "speak_expand"
    SPEAK_REASON = "speak_reason"
    SPEAK_EXAMPLE = "speak_example"
    SPEAK_KEYWORD = "speak_keyword"
    SPEAK_GUIDED = "speak_guided"
    SPEAK_SPONTANEOUS = "speak_spontaneous"
    SPEAK_FOLLOWUP = "speak_followup"


# Map stage → primary exercise type
STAGE_EXERCISE_TYPE: dict[int, RampExerciseType] = {
    0: RampExerciseType.SPEAK_ECHO,
    1: RampExerciseType.SPEAK_SUBSTITUTE,
    2: RampExerciseType.SPEAK_COMPLETE,
    3: RampExerciseType.SPEAK_ONE_SENTENCE,
    4: RampExerciseType.SPEAK_EXPAND,
    5: RampExerciseType.SPEAK_REASON,
    6: RampExerciseType.SPEAK_EXAMPLE,
    7: RampExerciseType.SPEAK_KEYWORD,
    8: RampExerciseType.SPEAK_GUIDED,
    9: RampExerciseType.SPEAK_SPONTANEOUS,
    10: RampExerciseType.SPEAK_FOLLOWUP,
}


# ---------------------------------------------------------------------------
# Support levels (§5)
# ---------------------------------------------------------------------------

class RampSupportLevel(int, Enum):
    """0 = no support → 7 = full translation/reference. §5"""
    NONE = 0
    TOPIC_ONLY = 1
    KEYWORDS = 2
    GUIDED_QUESTION = 3
    SENTENCE_STARTER = 4
    STRUCTURE_OUTLINE = 5
    EXAMPLE = 6
    TRANSLATION_REFERENCE = 7


# Independence weight multipliers — levels 6–7 are "direct answer" cues
SUPPORT_INDEPENDENCE_MULTIPLIER: dict[int, float] = {
    0: 1.00,   # fully independent
    1: 0.90,
    2: 0.75,
    3: 0.60,
    4: 0.50,
    5: 0.35,
    6: 0.20,   # example = reveals answer
    7: 0.10,   # translation = reveals answer
}


# ---------------------------------------------------------------------------
# Session state machine (§67)
# ---------------------------------------------------------------------------

class RampSessionState(str, Enum):
    IDLE = "idle"
    INTRO = "intro"
    PROMPTING = "prompting"
    PREPARING = "preparing"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    FEEDBACK = "feedback"
    RETRY = "retry"
    NEXT = "next"
    COMPLETED = "completed"


RAMP_STATE_TRANSITIONS: dict[RampSessionState, list[RampSessionState]] = {
    RampSessionState.IDLE: [RampSessionState.INTRO],
    RampSessionState.INTRO: [RampSessionState.PROMPTING],
    RampSessionState.PROMPTING: [RampSessionState.PREPARING, RampSessionState.RECORDING],
    RampSessionState.PREPARING: [RampSessionState.RECORDING],
    RampSessionState.RECORDING: [RampSessionState.TRANSCRIBING, RampSessionState.RETRY],
    RampSessionState.TRANSCRIBING: [RampSessionState.ANALYZING, RampSessionState.RETRY],
    RampSessionState.ANALYZING: [RampSessionState.FEEDBACK, RampSessionState.RETRY],
    RampSessionState.FEEDBACK: [RampSessionState.RETRY, RampSessionState.NEXT, RampSessionState.COMPLETED],
    RampSessionState.RETRY: [RampSessionState.PROMPTING, RampSessionState.RECORDING],
    RampSessionState.NEXT: [RampSessionState.PROMPTING],
    RampSessionState.COMPLETED: [RampSessionState.IDLE],
}


# ---------------------------------------------------------------------------
# Topic domains
# ---------------------------------------------------------------------------

class RampTopicDomain(str, Enum):
    PERSONAL = "personal"
    DAILY_LIFE = "daily_life"
    WORK = "work"
    STUDY = "study"
    OPINIONS = "opinions"
    PREFERENCES = "preferences"
    EXPERIENCES = "experiences"
    HYPOTHETICAL = "hypothetical"
    COMPARISON = "comparison"
    PROBLEM_SOLVING = "problem_solving"


# ---------------------------------------------------------------------------
# Elaboration signals (§21)
# ---------------------------------------------------------------------------

class ElaborationSignal(str, Enum):
    TOO_SHORT = "too_short"
    INCOMPLETE_SENTENCE = "incomplete_sentence"
    NO_REASON = "no_reason"
    NO_EXAMPLE = "no_example"
    CONTENT_WORD_ONLY = "content_word_only"
    REPETITION = "repetition"
    OFF_TOPIC = "off_topic"


# ---------------------------------------------------------------------------
# Follow-up types (§51)
# ---------------------------------------------------------------------------

class FollowUpType(str, Enum):
    FACT = "fact"
    WHY = "why"
    EXAMPLE = "example"
    COMPARISON = "comparison"
    HYPOTHETICAL = "hypothetical"


# ---------------------------------------------------------------------------
# Pydantic DTOs
# ---------------------------------------------------------------------------

class RampScaffold(BaseModel):
    """Concrete scaffold content rendered to the learner. §4"""
    support_level: int = 0
    topic: str | None = None
    keywords: list[str] = Field(default_factory=list)
    guided_questions: list[str] = Field(default_factory=list)
    sentence_starter: str | None = None
    structure_outline: list[str] = Field(default_factory=list)
    example_response: str | None = None
    translation_reference: str | None = None


class RampTaskSpec(BaseModel):
    """A single Mode 6 exercise task. §7"""
    exercise_type: RampExerciseType
    stage: int = Field(ge=0, le=10)
    topic: str
    topic_domain: RampTopicDomain = RampTopicDomain.DAILY_LIFE
    prompt_jp: str  # The Japanese prompt/instruction shown to learner
    prompt_vi: str | None = None  # Vietnamese context (optional)
    target_duration_sec: int = 0
    support_level: int = Field(default=0, ge=0, le=7)
    scaffold: RampScaffold = Field(default_factory=RampScaffold)
    # Echo-specific
    echo_sentence: str | None = None
    # Substitute-specific
    template_sentence: str | None = None
    substitution_variable: str | None = None
    # Expand-specific
    seed_sentence: str | None = None
    expansion_dimension: str | None = None  # "時間", "人", "理由", "detail"
    # Keyword-specific
    keywords_for_production: list[str] = Field(default_factory=list)
    # Session context
    session_topic_context: str | None = None
    previous_response: str | None = None  # For follow-up
    learning_targets: list[str] = Field(default_factory=list)
    is_retry: bool = False
    task_signature: str | None = None
    provider: str | None = None
    model: str | None = None


class RampGenerationInput(BaseModel):
    """Input to SpeakingRampGenerator. §7"""
    user_id: str
    learner_level: str = "N3"          # JLPT level (NOT assumed to equal speaking level)
    measured_speaking_level: str = "N4"  # Actual measured output level
    current_stage: int = Field(default=0, ge=0, le=10)
    support_level: int = Field(default=3, ge=0, le=7)
    recent_errors: list[dict[str, Any]] = Field(default_factory=list)
    recent_success_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    interests: list[str] = Field(default_factory=list)
    topic_history: list[str] = Field(default_factory=list)
    topic_domain: str | None = None
    difficulty: str = "normal"
    desired_duration_sec: int = 15
    session_goal: str | None = None
    previous_response: str | None = None   # For follow-up generation
    session_topic_context: str | None = None
    mastery: dict[str, float] = Field(default_factory=dict)
    is_retry: bool = False


class ElaborationPrompt(BaseModel):
    """Progressive elaboration cue. §20"""
    signal: ElaborationSignal
    cue_jp: str  # Japanese cue shown to learner
    cue_vi: str | None = None  # Vietnamese explanation
    step: int = 1  # 1=detail, 2=reason, 3=example, 4=compare


class FollowUpSpec(BaseModel):
    """A follow-up question for conversational endurance. §50–52"""
    question_jp: str
    question_vi: str | None = None
    follow_up_type: FollowUpType = FollowUpType.FACT
    depth_level: int = Field(default=1, ge=1, le=5)
    relates_to: str | None = None  # keyword from previous response


class RampScore(BaseModel):
    """Mode 6 composite score. §34 — weights differ from Mode 1/5."""
    # Weighted composite [0–100]
    overall: float = Field(ge=0, le=100)

    # Sub-dimensions
    production_accuracy: float = Field(ge=0, le=100, description="30% weight")
    independence: float = Field(ge=0, le=100, description="20% weight")
    completeness: float = Field(ge=0, le=100, description="15% weight")
    fluency: float = Field(ge=0, le=100, description="15% weight")
    elaboration: float = Field(ge=0, le=100, description="10% weight")
    reaction: float = Field(ge=0, le=100, description="10% weight")

    # Meta
    support_level_used: int = 0
    sentence_count: int = 0
    idea_count: int = 0
    speech_duration_ms: int | None = None
    filler_rate: float | None = None
    long_pause_count: int | None = None
    self_repair_count: int | None = None
    response_latency_ms: float | None = None
    independence_level: str = "independent"  # maps to IndependenceLevel

    @classmethod
    def compute(
        cls,
        production_accuracy: float,
        independence: float,
        completeness: float,
        fluency: float,
        elaboration: float,
        reaction: float,
        support_level_used: int = 0,
        **kwargs: Any,
    ) -> "RampScore":
        overall = (
            production_accuracy * 0.30
            + independence * 0.20
            + completeness * 0.15
            + fluency * 0.15
            + elaboration * 0.10
            + reaction * 0.10
        )
        return cls(
            overall=round(overall, 1),
            production_accuracy=production_accuracy,
            independence=independence,
            completeness=completeness,
            fluency=fluency,
            elaboration=elaboration,
            reaction=reaction,
            support_level_used=support_level_used,
            **kwargs,
        )


class RampAttemptFeedback(BaseModel):
    """Immediate feedback shown after each attempt. §37"""
    meaning_clear: bool = False
    grammar_ok: bool = False
    too_short: bool = False
    missing_reason: bool = False
    missing_example: bool = False
    incomplete_sentence: bool = False
    elaboration_prompt: ElaborationPrompt | None = None
    correction: str | None = None          # Corrected form (§53)
    correction_explanation: str | None = None
    badges: list[str] = Field(default_factory=list)  # ["✅ 意味明確", "⚠️ 短すぎ", ...]
    next_action: str = "retry"             # retry | next | elaborate
    ramp_score: RampScore | None = None
    followup: FollowUpSpec | None = None


class RampProgressSnapshot(BaseModel):
    """Learner progress metrics. §56–58"""
    user_id: str
    current_stage: int = 0
    current_support_level: int = 3

    # Speaking duration progress
    max_independent_duration_ms: int = 0
    avg_independent_duration_ms: float = 0.0
    duration_trend: list[int] = Field(default_factory=list)  # last 10 attempts

    # Quality metrics
    sentence_completeness_rate: float = 0.0   # % full sentences
    elaboration_success_rate: float = 0.0
    reason_success_rate: float = 0.0
    example_success_rate: float = 0.0
    followup_success_rate: float = 0.0

    # Fluency
    avg_filler_rate: float | None = None
    long_pause_trend: list[int] = Field(default_factory=list)
    self_repair_rate: float | None = None

    # Independence
    independent_success_rate: float = 0.0
    avg_response_latency_ms: float | None = None
    automaticity: float = 0.0

    total_attempts: int = 0
    total_sessions: int = 0


class RampSessionSummary(BaseModel):
    """End-of-session summary. §59"""
    session_id: str
    duration_minutes: float
    exercises_completed: int
    stage_start: int
    stage_end: int
    support_level_start: int
    support_level_end: int

    independent_speaking_pct: float
    avg_response_duration_ms: float
    full_sentence_rate: float
    elaboration_success_rate: float
    reason_example_rate: float
    long_pause_reduction_pct: float | None = None

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_recommendation: str = ""
    milestones_achieved: list[str] = Field(default_factory=list)


class RampSession(BaseModel):
    """In-memory session state (also persisted to DB). §67"""
    id: str
    user_id: str
    state: RampSessionState = RampSessionState.IDLE
    stage: int = 0
    support_level: int = 3
    session_goal: str | None = None
    desired_minutes: int = 15
    exercises_completed: int = 0
    topic_context: str | None = None   # sticky topic for follow-up continuity
    last_response: str | None = None
    attempt_results: list[dict[str, Any]] = Field(default_factory=list)
    stage_attempt_buffer: list[dict[str, Any]] = Field(default_factory=list)  # for progression gating
    started_at: str | None = None
    completed_at: str | None = None
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "RampStage",
    "STAGE_TARGET_DURATION_SEC",
    "STAGE_MIN_ATTEMPTS_BEFORE_CHANGE",
    "RampExerciseType",
    "STAGE_EXERCISE_TYPE",
    "RampSupportLevel",
    "SUPPORT_INDEPENDENCE_MULTIPLIER",
    "RampSessionState",
    "RAMP_STATE_TRANSITIONS",
    "RampTopicDomain",
    "ElaborationSignal",
    "FollowUpType",
    "RampScaffold",
    "RampTaskSpec",
    "RampGenerationInput",
    "ElaborationPrompt",
    "FollowUpSpec",
    "RampScore",
    "RampAttemptFeedback",
    "RampProgressSnapshot",
    "RampSessionSummary",
    "RampSession",
]
