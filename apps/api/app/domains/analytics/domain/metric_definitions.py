from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MetricKey(str, Enum):
    # Core Speaking Dimensions
    SPEAKING_FLUENCY = "fluency"
    NATURALNESS = "naturalness"
    GRAMMAR_ACCURACY = "grammar_accuracy"
    VOCABULARY_VARIETY = "vocabulary"
    
    # Pronunciation Sub-dimensions
    PRONUNCIATION_OVERALL = "pronunciation_overall"
    PITCH_ACCURACY = "pitch_accuracy"
    MORA_TIMING = "mora_timing"
    INTONATION = "intonation"
    
    # Conversational Dynamics
    RESPONSE_SPEED = "response_speed"
    FILLER_RATE = "filler_rate"
    SELF_CORRECTION = "self_correction"
    CONVERSATION_DEPTH = "conversation_depth"
    
    # Multimodal Practice & Curriculum
    SHADOWING_SCORE = "shadowing_score"
    LEARNING_CONSISTENCY = "learning_consistency"
    GOAL_PROGRESS = "goal_progress"
    EXERCISE_SUCCESS_RATE = "exercise_success_rate"
    MASTERY_DELTA = "mastery_delta"
    TRANSFER_RATE = "transfer_rate"

    # Reflex Speaking (Mode 1) Metrics
    REFLEX_REACTION_LATENCY = "reflex_reaction_latency"
    REFLEX_SEMANTIC_LATENCY = "reflex_semantic_latency"
    REFLEX_ACCURACY = "reflex_accuracy"
    REFLEX_AUTOMATICITY = "reflex_automaticity"
    REFLEX_PRESSURE_TOLERANCE = "reflex_pressure_tolerance"
    REFLEX_TIMEOUT_RATE = "reflex_timeout_rate"
    REFLEX_INDEPENDENT_SUCCESS = "reflex_independent_success"

    # Keigo Studio (Mode 2) Metrics
    KEIGO_ACCURACY = "keigo_accuracy"
    KEIGO_ROLE_ACCURACY = "keigo_role_accuracy"
    KEIGO_REGISTER_ACCURACY = "keigo_register_accuracy"
    KEIGO_KEIGO_ACCURACY = "keigo_keigo_accuracy"
    KEIGO_UCHI_SOTO_ACCURACY = "keigo_uchi_soto_accuracy"
    KEIGO_DOUBLE_KEIGO_RATE = "keigo_double_keigo_rate"
    KEIGO_NATURALNESS = "keigo_naturalness"
    KEIGO_CONTEXT_FIT = "keigo_context_fit"
    KEIGO_REACTION_LATENCY = "keigo_reaction_latency"
    KEIGO_AUTOMATICITY = "keigo_automaticity"

    # Pitch Lab (Mode 3) Metrics — reuse PITCH_ACCURACY etc but add lab-specific
    PITCH_MINIMAL_PAIR_ACCURACY = "pitch_minimal_pair_accuracy"
    PITCH_MORA_ACCURACY = "pitch_mora_accuracy"
    PITCH_DEVOICING_ACCURACY = "pitch_devoicing_accuracy"
    PITCH_CONTOUR_ACCURACY = "pitch_contour_accuracy"
    PITCH_RECOGNITION_ACCURACY = "pitch_recognition_accuracy"
    PITCH_LAB_AUTOMATICITY = "pitch_lab_automaticity"

    # Situational Roleplay (Mode 4) Metrics
    SITUATIONAL_TASK_COMPLETION = "situational_task_completion"
    SITUATIONAL_GOAL_SUCCESS_RATE = "situational_goal_success_rate"
    SITUATIONAL_INTENT_ACCURACY = "situational_intent_accuracy"
    SITUATIONAL_CONTEXT_FIT = "situational_context_fit"
    SITUATIONAL_RECOVERY_RATE = "situational_recovery_rate"
    SITUATIONAL_REACTION_LATENCY = "situational_reaction_latency"

    # Speaking Ramp (Mode 6) Metrics
    RAMP_INDEPENDENT_SUCCESS_RATE = "ramp.independent_success_rate"
    RAMP_FULL_SENTENCE_RATE = "ramp.full_sentence_rate"
    RAMP_AVG_RESPONSE_DURATION = "ramp.average_response_duration"
    RAMP_AVG_RESPONSE_LATENCY = "ramp.average_response_latency"
    RAMP_ELABORATION_SUCCESS_RATE = "ramp.elaboration_success_rate"
    RAMP_REASON_SUCCESS_RATE = "ramp.reason_success_rate"
    RAMP_EXAMPLE_SUCCESS_RATE = "ramp.example_success_rate"
    RAMP_FOLLOWUP_SUCCESS_RATE = "ramp.followup_success_rate"
    RAMP_FILLER_RATE = "ramp.filler_rate"
    RAMP_LONG_PAUSE_RATE = "ramp.long_pause_rate"
    RAMP_SELF_REPAIR_RATE = "ramp.self_repair_rate"
    RAMP_MAX_INDEPENDENT_DURATION = "ramp.max_independent_duration"
    RAMP_SUPPORT_LEVEL = "ramp.support_level"
    RAMP_AUTOMATICITY = "ramp.automaticity"


class TrendLabel(str, Enum):
    STRONGLY_IMPROVING = "strongly_improving"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    STRONGLY_DECLINING = "strongly_declining"
    PLATEAU = "plateau"
    INSUFFICIENT_DATA = "insufficient_data"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True)
class MetricDefinition:
    key: MetricKey
    name: str
    ja_name: str
    description: str
    unit: str
    category: str
    min_sample_size: int = 4
    comparison_method: str = "percentage_delta"
    version: str = "1.0.0"


METRIC_REGISTRY: dict[MetricKey, MetricDefinition] = {
    MetricKey.SPEAKING_FLUENCY: MetricDefinition(
        key=MetricKey.SPEAKING_FLUENCY,
        name="Speaking Fluency",
        ja_name="流暢さ",
        description="Pacing, turn continuity, and natural conversational flow without disruptive pauses.",
        unit="pts",
        category="speaking",
        min_sample_size=3,
    ),
    MetricKey.NATURALNESS: MetricDefinition(
        key=MetricKey.NATURALNESS,
        name="Naturalness & Nuance",
        ja_name="自然さ・敬語",
        description="Authentic Japanese phrasing, pragmatic appropriateness, sentence endings, and keigo nuances.",
        unit="%",
        category="speaking",
        min_sample_size=3,
    ),
    MetricKey.GRAMMAR_ACCURACY: MetricDefinition(
        key=MetricKey.GRAMMAR_ACCURACY,
        name="Grammar Production",
        ja_name="文法正確さ",
        description="Syntactic correctness, particle accuracy, verb conjugations, and structural coherence.",
        unit="%",
        category="grammar",
        min_sample_size=3,
    ),
    MetricKey.VOCABULARY_VARIETY: MetricDefinition(
        key=MetricKey.VOCABULARY_VARIETY,
        name="Vocabulary Variety",
        ja_name="語彙多様性",
        description="Lexical richness, collocation precision, and idiomatic expression usage.",
        unit="pts",
        category="vocabulary",
        min_sample_size=4,
    ),
    MetricKey.PRONUNCIATION_OVERALL: MetricDefinition(
        key=MetricKey.PRONUNCIATION_OVERALL,
        name="Pronunciation Overall",
        ja_name="総合発音精度",
        description="Acoustic clarity, phonemic match, mora duration, and pitch curve adherence.",
        unit="pts",
        category="pronunciation",
        min_sample_size=3,
    ),
    MetricKey.PITCH_ACCURACY: MetricDefinition(
        key=MetricKey.PITCH_ACCURACY,
        name="Pitch Accent Accuracy",
        ja_name="ピッチアクセント",
        description="F0 contour alignment with standard Tokyo pitch accent patterns (Atamadaka, Nakadaka, Odaka, Heiban).",
        unit="%",
        category="pronunciation",
        min_sample_size=3,
    ),
    MetricKey.MORA_TIMING: MetricDefinition(
        key=MetricKey.MORA_TIMING,
        name="Mora Timing & Rhythm",
        ja_name="拍感覚・モーラ比率",
        description="Isochronous Japanese mora rhythm, long vowel ratios (Chouon), sokuon (Q), and nasal (N).",
        unit="%",
        category="pronunciation",
        min_sample_size=3,
    ),
    MetricKey.INTONATION: MetricDefinition(
        key=MetricKey.INTONATION,
        name="Sentence Intonation",
        ja_name="文末イントネーション",
        description="Sentence-final pitch movement for questions, confirmations, assertions, and emotional nuances.",
        unit="%",
        category="pronunciation",
        min_sample_size=3,
    ),
    MetricKey.RESPONSE_SPEED: MetricDefinition(
        key=MetricKey.RESPONSE_SPEED,
        name="Response Latency",
        ja_name="発話初動速度",
        description="Elapsed time before initiating spoken response to conversational prompts, normalized by question complexity.",
        unit="ms",
        category="fluency",
        min_sample_size=4,
        comparison_method="inverse_ratio",
    ),
    MetricKey.FILLER_RATE: MetricDefinition(
        key=MetricKey.FILLER_RATE,
        name="Conversational Filler Rate",
        ja_name="フィラー頻度",
        description="Rate of natural vs unnatural filler utterances per minute of active speech (e.g. あの, えーと).",
        unit="fillers/min",
        category="fluency",
        min_sample_size=3,
        comparison_method="inverse_ratio",
    ),
    MetricKey.SELF_CORRECTION: MetricDefinition(
        key=MetricKey.SELF_CORRECTION,
        name="Self-Correction Success",
        ja_name="自己修正成功率",
        description="Frequency and resolution quality of spontaneous mid-speech self-corrections.",
        unit="%",
        category="fluency",
        min_sample_size=3,
    ),
    MetricKey.CONVERSATION_DEPTH: MetricDefinition(
        key=MetricKey.CONVERSATION_DEPTH,
        name="Conversation Depth",
        ja_name="会話維持力",
        description="Multi-turn topic elaboration, follow-up inquiry rate, and turn length maturity.",
        unit="turns/topic",
        category="speaking",
        min_sample_size=3,
    ),
    MetricKey.SHADOWING_SCORE: MetricDefinition(
        key=MetricKey.SHADOWING_SCORE,
        name="Shadowing Performance",
        ja_name="シャドーイング一致度",
        description="Temporal and acoustic synchronization with native Japanese audio tracks.",
        unit="pts",
        category="shadowing",
        min_sample_size=3,
    ),
    MetricKey.LEARNING_CONSISTENCY: MetricDefinition(
        key=MetricKey.LEARNING_CONSISTENCY,
        name="Practice Consistency",
        ja_name="学習継続性",
        description="Active practice frequency across calendar weeks and daily plan completion adherence.",
        unit="%",
        category="consistency",
        min_sample_size=7,
    ),
    MetricKey.GOAL_PROGRESS: MetricDefinition(
        key=MetricKey.GOAL_PROGRESS,
        name="Goal Progress",
        ja_name="目標達成度",
        description="Weighted milestone mastery progress across learning items tied to active learning goals.",
        unit="%",
        category="goal",
        min_sample_size=3,
    ),
    MetricKey.EXERCISE_SUCCESS_RATE: MetricDefinition(
        key=MetricKey.EXERCISE_SUCCESS_RATE,
        name="Exercise Success Rate",
        ja_name="ドリル正答率",
        description="Independent pass rate in structured curriculum exercises and drills.",
        unit="%",
        category="learning",
        min_sample_size=4,
    ),
    MetricKey.MASTERY_DELTA: MetricDefinition(
        key=MetricKey.MASTERY_DELTA,
        name="Mastery Growth Delta",
        ja_name="習熟度変化量",
        description="Net increase in estimated linguistic item mastery over the observation window.",
        unit="Δ pts",
        category="learning",
        min_sample_size=5,
    ),
    MetricKey.TRANSFER_RATE: MetricDefinition(
        key=MetricKey.TRANSFER_RATE,
        name="Spontaneous Transfer Rate",
        ja_name="自由発話定着率",
        description="Ratio of spontaneous conversation accuracy relative to supported drill accuracy for target patterns.",
        unit="%",
        category="learning",
        min_sample_size=4,
    ),
    MetricKey.REFLEX_REACTION_LATENCY: MetricDefinition(
        key=MetricKey.REFLEX_REACTION_LATENCY,
        name="Reflex Reaction Latency",
        ja_name="瞬発反応時間",
        description="Average time from prompt end to first voiced frame in reflex drills (ms). Lower is better.",
        unit="ms",
        category="reflex",
        min_sample_size=5,
        comparison_method="inverse_ratio",
    ),
    MetricKey.REFLEX_SEMANTIC_LATENCY: MetricDefinition(
        key=MetricKey.REFLEX_SEMANTIC_LATENCY,
        name="Semantic Response Latency",
        ja_name="意味応答時間",
        description="Time to first meaningful lexical content after filler removal.",
        unit="ms",
        category="reflex",
        min_sample_size=5,
        comparison_method="inverse_ratio",
    ),
    MetricKey.REFLEX_ACCURACY: MetricDefinition(
        key=MetricKey.REFLEX_ACCURACY,
        name="Reflex Accuracy Under Pressure",
        ja_name="瞬発正確さ",
        description="Correct response rate in timed reflex drills.",
        unit="%",
        category="reflex",
        min_sample_size=5,
    ),
    MetricKey.REFLEX_AUTOMATICITY: MetricDefinition(
        key=MetricKey.REFLEX_AUTOMATICITY,
        name="Reflex Automaticity",
        ja_name="自動化度",
        description="Mastery dimension: how quickly learner retrieves pattern under pressure.",
        unit="pts",
        category="reflex",
        min_sample_size=5,
    ),
    MetricKey.REFLEX_PRESSURE_TOLERANCE: MetricDefinition(
        key=MetricKey.REFLEX_PRESSURE_TOLERANCE,
        name="Pressure Tolerance",
        ja_name="プレッシャー耐性",
        description="Smallest timer where accuracy stays above 75% (ms).",
        unit="ms",
        category="reflex",
        min_sample_size=8,
    ),
    MetricKey.REFLEX_TIMEOUT_RATE: MetricDefinition(
        key=MetricKey.REFLEX_TIMEOUT_RATE,
        name="Reflex Timeout Rate",
        ja_name="タイムアウト率",
        description="Proportion of reflex attempts that timed out.",
        unit="%",
        category="reflex",
        min_sample_size=5,
        comparison_method="inverse_ratio",
    ),
    MetricKey.REFLEX_INDEPENDENT_SUCCESS: MetricDefinition(
        key=MetricKey.REFLEX_INDEPENDENT_SUCCESS,
        name="Independent Success Rate",
        ja_name="自立成功率",
        description="Share of reflex successes without hints.",
        unit="%",
        category="reflex",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_ACCURACY: MetricDefinition(
        key=MetricKey.KEIGO_ACCURACY,
        name="Keigo Accuracy",
        ja_name="敬語正確さ",
        description="Correct response rate in keigo drills.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_ROLE_ACCURACY: MetricDefinition(
        key=MetricKey.KEIGO_ROLE_ACCURACY,
        name="Uchi/Soto Role Accuracy",
        ja_name="ウチ・ソト判定",
        description="Correct identification of honorific direction based on Uchi/Soto.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_REGISTER_ACCURACY: MetricDefinition(
        key=MetricKey.KEIGO_REGISTER_ACCURACY,
        name="Register Accuracy",
        ja_name="レジスター適切さ",
        description="Correct register choice for situation.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_KEIGO_ACCURACY: MetricDefinition(
        key=MetricKey.KEIGO_KEIGO_ACCURACY,
        name="Keigo Form Accuracy",
        ja_name="敬語形式正確さ",
        description="Correct keigo morphological form.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_UCHI_SOTO_ACCURACY: MetricDefinition(
        key=MetricKey.KEIGO_UCHI_SOTO_ACCURACY,
        name="Uchi/Soto Accuracy",
        ja_name="内外判定正確さ",
        description="Correct Uchi/Soto perspective in context.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_DOUBLE_KEIGO_RATE: MetricDefinition(
        key=MetricKey.KEIGO_DOUBLE_KEIGO_RATE,
        name="Double Keigo Error Rate",
        ja_name="二重敬語誤用率",
        description="Rate of inappropriate double keigo.",
        unit="%",
        category="keigo",
        min_sample_size=5,
        comparison_method="inverse_ratio",
    ),
    MetricKey.KEIGO_NATURALNESS: MetricDefinition(
        key=MetricKey.KEIGO_NATURALNESS,
        name="Keigo Naturalness",
        ja_name="敬語自然さ",
        description="Naturalness of keigo phrasing in business context.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_CONTEXT_FIT: MetricDefinition(
        key=MetricKey.KEIGO_CONTEXT_FIT,
        name="Keigo Context Fit",
        ja_name="敬語文脈適合",
        description="Appropriateness of keigo for given social context.",
        unit="%",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.KEIGO_REACTION_LATENCY: MetricDefinition(
        key=MetricKey.KEIGO_REACTION_LATENCY,
        name="Keigo Reaction Latency",
        ja_name="敬語反応時間",
        description="Reaction latency for keigo drills.",
        unit="ms",
        category="keigo",
        min_sample_size=5,
        comparison_method="inverse_ratio",
    ),
    MetricKey.KEIGO_AUTOMATICITY: MetricDefinition(
        key=MetricKey.KEIGO_AUTOMATICITY,
        name="Keigo Automaticity",
        ja_name="敬語自動化度",
        description="Automaticity of keigo register selection under pressure.",
        unit="pts",
        category="keigo",
        min_sample_size=5,
    ),
    MetricKey.PITCH_MINIMAL_PAIR_ACCURACY: MetricDefinition(
        key=MetricKey.PITCH_MINIMAL_PAIR_ACCURACY,
        name="Minimal Pair Accuracy",
        ja_name="ミニマルペア正答率",
        description="Accuracy in pitch minimal pair discrimination.",
        unit="%",
        category="pitch",
        min_sample_size=5,
    ),
    MetricKey.PITCH_MORA_ACCURACY: MetricDefinition(
        key=MetricKey.PITCH_MORA_ACCURACY,
        name="Mora Length Accuracy",
        ja_name="モーラ長正確さ",
        description="Accuracy in mora/length discrimination.",
        unit="%",
        category="pitch",
        min_sample_size=5,
    ),
    MetricKey.PITCH_LAB_AUTOMATICITY: MetricDefinition(
        key=MetricKey.PITCH_LAB_AUTOMATICITY,
        name="Pitch Lab Automaticity",
        ja_name="ピッチ自動化度",
        description="Automaticity of pitch pattern production under pressure.",
        unit="pts",
        category="pitch",
        min_sample_size=5,
    ),
    MetricKey.SITUATIONAL_TASK_COMPLETION: MetricDefinition(
        key=MetricKey.SITUATIONAL_TASK_COMPLETION,
        name="Task Completion",
        ja_name="タスク達成率",
        description="Rate of situational goals completed.",
        unit="%",
        category="situational",
        min_sample_size=5,
    ),
    MetricKey.SITUATIONAL_GOAL_SUCCESS_RATE: MetricDefinition(
        key=MetricKey.SITUATIONAL_GOAL_SUCCESS_RATE,
        name="Goal Success Rate",
        ja_name="目標成功率",
        description="Rate of goals achieved in situational roleplay.",
        unit="%",
        category="situational",
        min_sample_size=5,
    ),
    MetricKey.SITUATIONAL_INTENT_ACCURACY: MetricDefinition(
        key=MetricKey.SITUATIONAL_INTENT_ACCURACY,
        name="Intent Accuracy",
        ja_name="意図正確さ",
        description="Accuracy of intent recognition in situational context.",
        unit="%",
        category="situational",
        min_sample_size=5,
    ),
    MetricKey.SITUATIONAL_CONTEXT_FIT: MetricDefinition(
        key=MetricKey.SITUATIONAL_CONTEXT_FIT,
        name="Context Fit",
        ja_name="文脈適合",
        description="Contextual appropriateness in situational roleplay.",
        unit="%",
        category="situational",
        min_sample_size=5,
    ),
    MetricKey.SITUATIONAL_RECOVERY_RATE: MetricDefinition(
        key=MetricKey.SITUATIONAL_RECOVERY_RATE,
        name="Recovery Rate",
        ja_name="リカバリー率",
        description="Success rate in conversational repair.",
        unit="%",
        category="situational",
        min_sample_size=5,
    ),
    MetricKey.SITUATIONAL_REACTION_LATENCY: MetricDefinition(
        key=MetricKey.SITUATIONAL_REACTION_LATENCY,
        name="Situational Reaction Latency",
        ja_name="場面反応時間",
        description="Reaction latency in situational roleplay.",
        unit="ms",
        category="situational",
        min_sample_size=5,
        comparison_method="inverse_ratio",
    ),
}


@dataclass
class MetricValue:
    metric_key: MetricKey
    value: float
    baseline: float | None = None
    change: float | None = None
    sample_size: int = 0
    confidence: ConfidenceLevel = ConfidenceLevel.INSUFFICIENT
    period: str = "30d"
    trend: TrendLabel = TrendLabel.INSUFFICIENT_DATA
    metric_version: str = "1.0.0"
    extra_metadata: dict[str, Any] = field(default_factory=dict)
