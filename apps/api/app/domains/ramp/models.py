"""Mode 6 — RampSession SQLAlchemy model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if True:  # TYPE_CHECKING guard to avoid circular import
    pass


class RampSessionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted Mode 6 session record."""

    __tablename__ = "ramp_sessions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    state: Mapped[str] = mapped_column(
        String(30), default="idle", nullable=False, index=True
    )

    # Progression state
    stage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    support_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    stage_start: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    support_level_start: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Session config
    desired_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    session_goal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    topic_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progress counters
    exercises_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    exercises_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Aggregate metrics (updated after each attempt)
    independent_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    full_sentence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    elaboration_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    example_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    followup_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_speech_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_speech_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # JSON blobs
    attempt_results: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    stage_attempt_buffer: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    milestones_achieved: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
