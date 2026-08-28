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
    from app.domains.users.models import User


class PronunciationAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Stores individual pronunciation recordings, scores, feedback, and acoustic metadata."""
    __tablename__ = "pronunciation_attempts"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    turn_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversation_turns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reference_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_reading: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    target_type: Mapped[str] = mapped_column(String(30), default="sentence", nullable=False)
    reference_type: Mapped[str] = mapped_column(String(30), default="synthetic", nullable=False)

    analysis_status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False, index=True
    )  # pending, processing, completed, failed

    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_confidence: Mapped[str | None] = mapped_column(String(30), nullable=True)
    score_interpretation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    engine_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)

    scores_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    feedback_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    acoustic_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    session: Mapped["ConversationSession | None"] = relationship("ConversationSession")
    turn: Mapped["ConversationTurn | None"] = relationship("ConversationTurn")


class PronunciationPracticeTarget(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Curated and auto-generated pronunciation practice targets based on learner weaknesses."""
    __tablename__ = "pronunciation_practice_targets"

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    target_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_reading: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str] = mapped_column(String(30), default="word", nullable=False)  # word, sentence, pitch
    difficulty: Mapped[str] = mapped_column(String(30), default="beginner", nullable=False)
    weak_area_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), default="phoneme", nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
