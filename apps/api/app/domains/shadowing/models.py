from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.learning.models import Exercise
    from app.domains.users.models import User


class ShadowingVideo(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores YouTube video metadata, overall speaking difficulty, and import status without storing full raw media."""
    __tablename__ = "shadowing_videos"

    video_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(30), default="ja", nullable=False)
    source_status: Mapped[str] = mapped_column(String(50), default="available", nullable=False)

    import_status: Mapped[str] = mapped_column(
        String(50), default="queued", nullable=False, index=True
    )  # queued, fetching_metadata, resolving_transcript, transcribing, segmenting, analyzing, ready, partial, failed
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    overall_difficulty: Mapped[str] = mapped_column(String(30), default="normal", nullable=False)
    summary_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    transcripts: Mapped[list["ShadowingTranscript"]] = relationship(
        "ShadowingTranscript",
        back_populates="video",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    segments: Mapped[list["ShadowingSegment"]] = relationship(
        "ShadowingSegment",
        back_populates="video",
        cascade="all, delete-orphan",
        order_by="ShadowingSegment.sequence",
        lazy="selectin",
    )


class ShadowingTranscript(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Versioned transcript associated with a video, sourced from YouTube captions or Faster-Whisper."""
    __tablename__ = "shadowing_transcripts"

    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(50), default="youtube", nullable=False)  # youtube, faster_whisper
    source_version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(30), default="ja", nullable=False)
    quality: Mapped[str] = mapped_column(String(30), default="high", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    transcript_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_data_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    video: Mapped["ShadowingVideo"] = relationship("ShadowingVideo", back_populates="transcripts")
    segments: Mapped[list["ShadowingSegment"]] = relationship(
        "ShadowingSegment",
        back_populates="transcript",
        cascade="all, delete-orphan",
        order_by="ShadowingSegment.sequence",
        lazy="selectin",
    )


class ShadowingSegment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A precise sentence-level timestamped segment suitable for sentence looping and shadowing analysis."""
    __tablename__ = "shadowing_segments"

    transcript_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_transcripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    start_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    end_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    reading: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(30), default="ja", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    speaker_id: Mapped[str] = mapped_column(String(50), default="Speaker A", nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    difficulty_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    vocabulary_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    grammar_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    expressions_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    candidate_categories_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    recommendation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    video: Mapped["ShadowingVideo"] = relationship("ShadowingVideo", back_populates="segments")
    transcript: Mapped["ShadowingTranscript"] = relationship("ShadowingTranscript", back_populates="segments")


class ShadowingImportJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks stateful background ingestion and multi-stage analysis pipeline for imported YouTube videos."""
    __tablename__ = "shadowing_import_jobs"

    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage: Mapped[str] = mapped_column(
        String(50), default="queued", nullable=False
    )  # metadata, transcript, whisper_fallback, segmentation, analysis, candidate_selection, done
    status: Mapped[str] = mapped_column(
        String(50), default="queued", nullable=False, index=True
    )  # queued, processing, completed, partial, failed
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stage_statuses_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    video: Mapped["ShadowingVideo"] = relationship("ShadowingVideo")
    user: Mapped["User"] = relationship("User")


class ShadowingBookmark(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-saved segment bookmarks with personal notes."""
    __tablename__ = "shadowing_bookmarks"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    video: Mapped["ShadowingVideo"] = relationship("ShadowingVideo")
    segment: Mapped["ShadowingSegment"] = relationship("ShadowingSegment")

    __table_args__ = (
        UniqueConstraint("user_id", "segment_id", name="uq_shadowing_bookmark_user_segment"),
    )


class ShadowingSegmentProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Learner progress per segment, connecting shadowing practice directly to Phase 7 Exercise and Mastery."""
    __tablename__ = "shadowing_segment_progress"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_segments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("exercises.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    listen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shadow_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    mastery: Mapped[str] = mapped_column(
        String(30), default="discovered", nullable=False, index=True
    )  # discovered, selected, practicing, comfortable, mastered
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    video: Mapped["ShadowingVideo"] = relationship("ShadowingVideo")
    segment: Mapped["ShadowingSegment"] = relationship("ShadowingSegment")
    exercise: Mapped["Exercise | None"] = relationship("Exercise")

    __table_args__ = (
        UniqueConstraint("user_id", "segment_id", name="uq_shadowing_progress_user_segment"),
    )


class ShadowingVideoProgress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Aggregated video-level progress for user history, resume playback, and completion tracking."""
    __tablename__ = "shadowing_video_progress"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    video_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("shadowing_videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    watch_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shadow_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mastery_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    segments_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_practice_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_position_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    video: Mapped["ShadowingVideo"] = relationship("ShadowingVideo")

    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_shadowing_video_progress_user_video"),
    )
