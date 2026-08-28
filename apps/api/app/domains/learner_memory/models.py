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
    from app.domains.conversation.models import ConversationSession, ConversationTurn
    from app.domains.conversation_intelligence.models import (
        AnalysisCorrection,
        TurnAnalysis,
    )
    from app.domains.users.models import User


class LearnerMemory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Layer 2 — Cross-session persistent learner memory."""
    __tablename__ = "learner_memories"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    evidence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="SHOULD_FIX", nullable=False)
    severity_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False, index=True)
    mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    trend: Mapped[str] = mapped_column(String(30), default="new", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False, index=True)
    is_regression: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    contexts_used: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    evidences: Mapped[list["MemoryEvidence"]] = relationship(
        "MemoryEvidence",
        back_populates="memory",
        cascade="all, delete-orphan",
        order_by="desc(MemoryEvidence.created_at)",
        lazy="selectin",
    )
    feedbacks: Mapped[list["MemoryFeedback"]] = relationship(
        "MemoryFeedback",
        back_populates="memory",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_learner_memory_user_key"),
    )


class MemoryEvidence(Base, UUIDPrimaryKeyMixin):
    """Granular evidence record linking a persistent memory to a concrete session/turn/correction."""
    __tablename__ = "memory_evidences"

    memory_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("learner_memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversation_turns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    turn_analysis_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("turn_analyses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    correction_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("analysis_corrections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)  # error_observation, correct_observation, session_pattern, strength, goal
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    original_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    memory: Mapped["LearnerMemory"] = relationship("LearnerMemory", back_populates="evidences")
    session: Mapped["ConversationSession"] = relationship("ConversationSession")
    turn: Mapped["ConversationTurn | None"] = relationship("ConversationTurn")
    turn_analysis: Mapped["TurnAnalysis | None"] = relationship("TurnAnalysis")
    correction: Mapped["AnalysisCorrection | None"] = relationship("AnalysisCorrection")

    __table_args__ = (
        UniqueConstraint("memory_id", "session_id", "turn_id", "correction_id", "evidence_type", name="uq_memory_evidence_source"),
    )


class LearnerProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Layer 3 — Aggregate long-term learner profile."""
    __tablename__ = "learner_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    overall_level: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)
    speaking_level: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)
    fluency_level: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)
    grammar_level: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)
    vocabulary_level: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)
    naturalness_level: Mapped[str] = mapped_column(String(30), default="intermediate", nullable=False)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    level_confidence: Mapped[str] = mapped_column(String(30), default="insufficient_evidence", nullable=False)

    total_sessions_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_turns_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_speed_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_focus: Mapped[str | None] = mapped_column(String(150), nullable=True)

    strengths: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    learning_goals: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    summary_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_recalculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")


class MemoryFeedback(Base, UUIDPrimaryKeyMixin):
    """User feedback or correction controls for persistent memories."""
    __tablename__ = "memory_feedback"

    memory_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("learner_memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)  # dismiss, mark_inaccurate, restore
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    memory: Mapped["LearnerMemory"] = relationship("LearnerMemory", back_populates="feedbacks")
