from datetime import datetime
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class PronunciationAnalysisPolicy(str, Enum):
    OFF = "off"
    BASIC = "basic"
    DEEP = "deep"


class TargetType(str, Enum):
    WORD = "word"
    PHRASE = "phrase"
    SENTENCE = "sentence"
    CONVERSATION_LINE = "conversation_line"
    CUSTOM = "custom"


class ReferenceType(str, Enum):
    HUMAN = "human"
    SYNTHETIC = "synthetic"  # VOICEVOX or TTS
    YOUTUBE = "youtube"
    UNKNOWN = "unknown"


class AnalysisConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class PitchAccentPattern(str, Enum):
    HEIBAN = "heiban"        # Flat (0)
    ATAMADAKA = "atamadaka"  # Head-high (1)
    NAKADAKA = "nakadaka"    # Middle-high (2...)
    ODAKA = "odaka"          # Tail-high (drop on particle)
    UNKNOWN = "unknown"


class AudioQualityReport(BaseModel):
    is_usable: bool = True
    signal_level_rms: float = 0.0
    is_clipped: bool = False
    snr_estimate_db: float | None = None
    silence_ratio: float = 0.0
    duration_ms: int = 0
    issues: list[str] = Field(default_factory=list)
    guidance: str | None = None


class MoraUnit(BaseModel):
    mora_index: int
    kana: str
    phonemes: list[str] = Field(default_factory=list)
    is_special: bool = False  # small tsu, long vowel, n, yoon
    special_type: str | None = None  # gemination, long_vowel, nasal, contracted
    expected_duration_ms: int | None = None
    actual_duration_ms: int | None = None
    duration_ratio: float | None = None
    score: float | None = None
    issue: str | None = None
    confidence: float = 1.0


class PitchPoint(BaseModel):
    timestamp_ms: int
    frequency_hz: float
    normalized_semitones: float
    is_voiced: bool = True
    confidence: float = 1.0


class PitchCurve(BaseModel):
    points: list[PitchPoint] = Field(default_factory=list)
    speaker_f0_mean: float | None = None
    speaker_f0_std: float | None = None
    voiced_ratio: float = 0.0
    confidence: float = 1.0
    normalization_method: str = "semitone_zscore"


class AlignmentSegment(BaseModel):
    text: str
    mora_list: list[str] = Field(default_factory=list)
    start_ms: int
    end_ms: int
    confidence: float = 1.0


class AlignmentResult(BaseModel):
    segments: list[AlignmentSegment] = Field(default_factory=list)
    mora_units: list[MoraUnit] = Field(default_factory=list)
    confidence_level: AnalysisConfidenceLevel = AnalysisConfidenceLevel.HIGH
    unmatched_regions: list[tuple[int, int]] = Field(default_factory=list)
    total_speech_duration_ms: int = 0


class PhonemeAssessment(BaseModel):
    mora_index: int
    kana: str
    target_phonemes: list[str] = Field(default_factory=list)
    detected_sound_category: str | None = None
    score: float = 100.0
    confidence: float = 1.0
    issue_type: str | None = None
    tip: str | None = None


class MoraTimingAssessment(BaseModel):
    overall_score: float = 100.0
    confidence: float = 1.0
    mora_units: list[MoraUnit] = Field(default_factory=list)
    speech_rate_mora_per_sec: float = 0.0
    rhythm_regularity_score: float = 100.0
    top_timing_issues: list[str] = Field(default_factory=list)


class PitchAssessment(BaseModel):
    overall_score: float = 100.0
    confidence: float = 1.0
    accent_pattern_target: PitchAccentPattern = PitchAccentPattern.UNKNOWN
    accent_pattern_observed: PitchAccentPattern = PitchAccentPattern.UNKNOWN
    pattern_matched: bool = True
    pitch_curve: PitchCurve | None = None
    reference_pitch_curve: PitchCurve | None = None
    explanation: str | None = None


class RhythmAssessment(BaseModel):
    overall_score: float = 100.0
    confidence: float = 1.0
    speech_rate_mora_per_sec: float = 0.0
    reference_rate_mora_per_sec: float | None = None
    pause_count: int = 0
    hesitation_count: int = 0
    naturalness_score: float = 100.0
    details: dict[str, Any] = Field(default_factory=dict)


class IntonationAssessment(BaseModel):
    overall_score: float = 100.0
    confidence: float = 1.0
    sentence_final_type: str = "statement_falling"  # question_rising, statement_falling, exclamatory
    is_sentence_final_natural: bool = True
    phrase_boundaries_count: int = 0
    contour_smoothness: float = 100.0
    explanation: str | None = None


class PronunciationScoreComponent(BaseModel):
    score: float
    confidence: float
    weight: float
    available: bool = True
    interpretation: str = "Good"  # Excellent, Very Good, Good, Developing, Needs Attention


class PronunciationFeedbackItem(BaseModel):
    issue_key: str
    category: str
    severity: str  # MUST_FIX, SHOULD_FIX, NATIVE_ALTERNATIVE, STRENGTH
    title: str
    explanation: str
    practice_tip: str
    target_snippet: str | None = None
    detected_snippet: str | None = None
    can_listen_reference: bool = True
    can_listen_user: bool = True
    audio_timestamp_ms: int | None = None


class PronunciationResult(BaseModel):
    overall_score: float
    overall_confidence: AnalysisConfidenceLevel
    score_interpretation: str  # Excellent, Very Good, Good, Developing, Needs Attention
    
    # Subscores (partial nulls supported)
    phoneme_score: PronunciationScoreComponent | None = None
    mora_timing_score: PronunciationScoreComponent | None = None
    pitch_score: PronunciationScoreComponent | None = None
    rhythm_score: PronunciationScoreComponent | None = None
    intonation_score: PronunciationScoreComponent | None = None

    # Deep assessments
    phoneme_assessment: list[PhonemeAssessment] | None = None
    mora_assessment: MoraTimingAssessment | None = None
    pitch_assessment: PitchAssessment | None = None
    rhythm_assessment: RhythmAssessment | None = None
    intonation_assessment: IntonationAssessment | None = None
    
    # Quality & VAD
    audio_quality: AudioQualityReport | None = None
    
    # User-facing feedback
    top_issues: list[PronunciationFeedbackItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    practice_recommendation: str | None = None
    
    # Metadata & Versioning
    engine_version: str = "1.0.0"
    scoring_version: str = "1.0.0"
    reference_type: ReferenceType = ReferenceType.UNKNOWN
    partial_reasons: list[str] = Field(default_factory=list)


class PronunciationTarget(BaseModel):
    reference_text: str
    expected_reading: str | None = None
    target_type: TargetType = TargetType.SENTENCE
    reference_type: ReferenceType = ReferenceType.SYNTHETIC
    reference_audio_bytes: bytes | None = None
    voicevox_speaker_id: int | None = 1
