from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domains.shadowing.contracts import (
    CandidateCategory,
    DifficultyReport,
    ExtractedGrammar,
    ExtractedVocabulary,
    NaturalExpression,
    ShadowingCandidate,
    SpeakingDifficulty,
    TranscriptSegmentDTO,
    VideoStatus,
)


class VideoImportRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL (watch, youtu.be, or shorts)")
    custom_whisper_model: str | None = Field(
        default=None, description="Optional custom STT model for Whisper fallback (e.g. 'base', 'small', 'medium', 'large-v3')"
    )


class VideoImportResponse(BaseModel):
    video_id: str
    canonical_video_id: str
    job_id: str
    status: VideoStatus
    message: str
    is_existing: bool = False


class ShadowingVideoDTO(BaseModel):
    id: str
    video_id: str
    url: str
    canonical_url: str
    title: str
    channel_name: str
    channel_id: str | None = None
    thumbnail_url: str | None = None
    duration_seconds: int = 0
    language: str = "ja"
    import_status: VideoStatus
    overall_difficulty: SpeakingDifficulty = SpeakingDifficulty.NORMAL
    summary_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class ShadowingSegmentProgressDTO(BaseModel):
    id: str
    segment_id: str
    exercise_id: str | None = None
    listen_count: int = 0
    shadow_attempts: int = 0
    best_score: float | None = None
    mastery: str = "discovered"
    last_practiced_at: datetime | None = None


class ShadowingVideoProgressDTO(BaseModel):
    watch_progress: float = 0.0
    shadow_progress: float = 0.0
    mastery_progress: float = 0.0
    segments_completed: int = 0
    total_practice_time_seconds: int = 0
    best_score: float | None = None
    last_position_seconds: float = 0.0
    last_opened_at: datetime | None = None


class ShadowingVideoDetailDTO(ShadowingVideoDTO):
    segments_count: int = 0
    recommended_count: int = 0
    segments: list[TranscriptSegmentDTO] = Field(default_factory=list)
    recommended_segments: list[ShadowingCandidate] = Field(default_factory=list)
    progress: ShadowingVideoProgressDTO | None = None


class ShadowingVideoListResponse(BaseModel):
    videos: list[ShadowingVideoDTO] = Field(default_factory=list)
    total: int = 0


class BookmarkRequest(BaseModel):
    note: str | None = None


class BookmarkDTO(BaseModel):
    id: str
    user_id: str
    video_id: str
    segment_id: str
    note: str | None = None
    created_at: datetime


class SegmentPracticeStartRequest(BaseModel):
    shadowing_mode: str = "shadow"  # listen, shadow, listen_shadow, repeat


class SegmentPracticeStartResponse(BaseModel):
    exercise_id: str
    attempt_id: str
    segment_id: str
    video_id: str
    reference_text: str
    expected_reading: str | None = None
    start_time: float
    end_time: float
    speaker_id: str = "Speaker A"


class SegmentPracticeCompleteRequest(BaseModel):
    exercise_id: str
    attempt_id: str
    audio_base64: str
    shadowing_mode: str = "shadow"
    playback_speed: float = 1.0
    client_transcript: str | None = None


class SegmentPracticeCompleteResponse(BaseModel):
    exercise_id: str
    attempt_id: str
    segment_id: str
    target_text: str | None = None
    user_transcript: str | None = None
    score: float
    timing_score: float
    pronunciation_score: float
    rhythm_score: float
    accuracy_score: float
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    top_issues: list[dict[str, Any]] = Field(default_factory=list)
    mastery: str = "practicing"
    mastery_delta: float = 0.0
    review_scheduled_at: datetime | None = None


class SegmentTranslateRequest(BaseModel):
    target_language: str = "vi"  # vi, en, ja


class SegmentTranslateResponse(BaseModel):
    segment_id: str
    source_text: str
    target_language: str
    translated_text: str
    explanation: str | None = None


class ShadowingJobStatusDTO(BaseModel):
    job_id: str
    video_id: str
    stage: str
    status: str
    attempts: int = 0
    stage_statuses: dict[str, Any] | None = None
    error_type: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CreateLessonRequest(BaseModel):
    time_budget_minutes: int = 15
    mode: str = "quick_shadow"  # quick_shadow, deep_shadow, pronunciation_focus, naturalness_focus, speed_challenge


class ReprocessVideoRequest(BaseModel):
    scope: str = "all"  # all, analysis, transcript
    custom_whisper_model: str | None = None
