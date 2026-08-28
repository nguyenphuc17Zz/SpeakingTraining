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
    from app.domains.conversation.models import ConversationSession
    from app.domains.users.models import User


class SessionAnalyticsRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Derived analytics produced after a conversation or exercise session completes."""
    __tablename__ = "session_analytics_records"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    speaking_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_turns_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assistant_turns_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    grammar_error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    naturalness_issue_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    filler_rate_per_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    self_correction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topic_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    pronunciation_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    session: Mapped["ConversationSession"] = relationship("ConversationSession")
    user: Mapped["User"] = relationship("User")


class LearnerAnalyticsSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Precomputed daily snapshot of learner metrics, trends, and bottleneck state."""
    __tablename__ = "learner_analytics_snapshots"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    metric_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    trends_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    bottleneck_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    practice_distribution_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_analytics_snapshot_user_date"),
    )


class WeeklyReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Weekly deterministic facts summary with optional AI personalized narrative."""
    __tablename__ = "weekly_reviews"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_start: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD (Monday)
    facts_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_weekly_review_user_week"),
    )


class InsightRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Active diagnostic insights and actionable suggestions."""
    __tablename__ = "insight_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    metric_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    action_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_target_key: Mapped[str | None] = mapped_column(String(120), nullable=True)

    evidence_keys_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source_period: Mapped[str] = mapped_column(String(20), default="30d", nullable=False)

    lifecycle: Mapped[str] = mapped_column(
        String(20), default="new", nullable=False, index=True
    )  # new, seen, acted_on, expired
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class CoachConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit log of user questions and Personal AI Coach grounded answers."""
    __tablename__ = "coach_conversations"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)

    key_points_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    evidence_refs_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    recommendations_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    context_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    feedback: Mapped[list["CoachFeedback"]] = relationship(
        "CoachFeedback",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CoachFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User feedback for coach explanations."""
    __tablename__ = "coach_feedbacks"

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("coach_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[str] = mapped_column(String(30), nullable=False)  # helpful, not_helpful, incorrect
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    conversation: Mapped["CoachConversation"] = relationship("CoachConversation", back_populates="feedback")
    user: Mapped["User"] = relationship("User")


class RecommendationRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tracks coach recommendation delivery and eventual learner execution outcomes."""
    __tablename__ = "recommendation_records"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("coach_conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)  # conversation, drill, shadowing, pronunciation
    target: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    status: Mapped[str] = mapped_column(
        String(30), default="recommended", nullable=False, index=True
    )  # recommended, accepted, started, completed, skipped
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome_metrics_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
