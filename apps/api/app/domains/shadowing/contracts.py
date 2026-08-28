from datetime import datetime
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    FETCHING_METADATA = "fetching_metadata"
    RESOLVING_TRANSCRIPT = "resolving_transcript"
    TRANSCRIBING = "transcribing"
    SEGMENTING = "segmenting"
    ANALYZING = "analyzing"
    READY = "ready"
    PARTIAL = "partial"
    FAILED = "failed"


class TranscriptSource(str, Enum):
    YOUTUBE = "youtube"
    FASTER_WHISPER = "faster_whisper"


class TranscriptQuality(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SpeakingDifficulty(str, Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    VERY_HARD = "very_hard"


class CandidateCategory(str, Enum):
    BEST_FOR_BEGINNER = "BEST_FOR_BEGINNER"
    BEST_FOR_PRONUNCIATION = "BEST_FOR_PRONUNCIATION"
    BEST_FOR_NATURALNESS = "BEST_FOR_NATURALNESS"
    BEST_FOR_SPEED = "BEST_FOR_SPEED"
    BEST_FOR_WORKPLACE = "BEST_FOR_WORKPLACE"
    BEST_FOR_CHALLENGE = "BEST_FOR_CHALLENGE"


class ShadowingMode(str, Enum):
    LISTEN = "listen"
    SHADOW = "shadow"
    LISTEN_SHADOW = "listen_shadow"
    REPEAT = "repeat"
    AB_LOOP = "ab_loop"


class ShadowingVideoMetadata(BaseModel):
    video_id: str
    url: str
    canonical_url: str
    title: str
    channel_name: str
    channel_id: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int = 0
    published_at: datetime | None = None
    description: str | None = None
    language: str | None = "ja"
    source_status: str = "available"  # available, private, unavailable, restricted
    metadata_fetched_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptQualityReport(BaseModel):
    quality: TranscriptQuality = TranscriptQuality.HIGH
    language: str = "Japanese"
    has_timestamps: bool = True
    confidence: float = 1.0
    issues: list[str] = Field(default_factory=list)


class SpeakerInfo(BaseModel):
    id: str  # e.g. "Speaker A", "Speaker B"
    label: str
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedVocabulary(BaseModel):
    word: str
    reading: str
    meaning: str
    part_of_speech: str | None = None
    difficulty: str | None = "N3"
    frequency: str | None = None
    context_sentence: str
    source_segment_id: str | None = None
    source_text_span: str | None = None
    learning_value: float = 0.8  # 0.0 - 1.0


class ExtractedGrammar(BaseModel):
    pattern: str
    level: str = "N3"
    meaning: str
    context: str
    example: str | None = None
    source_segment_id: str | None = None
    source_text_span: str | None = None
    learning_value: float = 0.8


class NaturalExpression(BaseModel):
    expression: str
    reading: str | None = None
    meaning: str
    category: str  # filler, sentence_ending, slang, collocation, discourse_marker, reaction
    context_sentence: str
    source_segment_id: str | None = None
    source_text_span: str | None = None
    learning_value: float = 0.85


class DifficultyReport(BaseModel):
    lexical_score: float = 0.5
    grammar_score: float = 0.5
    speed_mora_per_sec: float = 6.0
    pronunciation_complexity: float = 0.5
    sentence_density: float = 0.5
    context_naturalness: float = 0.7
    overall_difficulty: SpeakingDifficulty = SpeakingDifficulty.NORMAL
    reasons: list[str] = Field(default_factory=list)


class TranscriptSegmentDTO(BaseModel):
    id: str
    video_id: str
    start_time: float  # seconds
    end_time: float    # seconds
    text: str
    normalized_text: str
    reading: str | None = None
    ruby: list[dict[str, Any]] = Field(default_factory=list)
    language: str = "ja"
    confidence: float = 1.0
    speaker_id: str = "Speaker A"
    sequence: int = 0
    duration: float = 0.0
    difficulty: DifficultyReport | None = None
    vocabulary: list[ExtractedVocabulary] = Field(default_factory=list)
    grammar: list[ExtractedGrammar] = Field(default_factory=list)
    expressions: list[NaturalExpression] = Field(default_factory=list)
    candidate_categories: list[CandidateCategory] = Field(default_factory=list)
    recommendation_score: float | None = None
    recommendation_reason: str | None = None


class ShadowingCandidate(BaseModel):
    segment_id: str
    video_id: str
    start_time: float
    end_time: float
    text: str
    reading: str | None = None
    ruby: list[dict[str, Any]] = Field(default_factory=list)
    speaker_id: str = "Speaker A"
    score: float = 0.8
    categories: list[CandidateCategory] = Field(default_factory=list)
    reason: str
    target_skill: str = "fluency"
    difficulty: SpeakingDifficulty = SpeakingDifficulty.NORMAL
    matched_weakness: str | None = None
    matched_goal: str | None = None


class ShadowingLesson(BaseModel):
    id: str
    video_id: str
    title: str
    goal: str
    mode: str = "quick_shadow"  # quick_shadow, deep_shadow, pronunciation_focus, naturalness_focus, speed_challenge
    estimated_minutes: int = 15
    difficulty: SpeakingDifficulty = SpeakingDifficulty.NORMAL
    segments: list[TranscriptSegmentDTO] = Field(default_factory=list)


class ShadowingAttemptContext(BaseModel):
    video_id: str
    segment_id: str
    reference_text: str
    reference_start: float
    reference_end: float
    speaker_id: str = "Speaker A"
    shadowing_mode: ShadowingMode = ShadowingMode.SHADOW


class VideoMetadataProvider(Protocol):
    """Protocol for fetching video metadata from YouTube or other video providers."""
    async def get_metadata(self, video_id: str) -> ShadowingVideoMetadata:
        ...


class VideoTranscriptProvider(Protocol):
    """Protocol for fetching or generating timestamped Japanese transcripts."""
    async def get_transcript(self, video_id: str) -> list[dict[str, Any]]:
        ...
