from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.conversation.models import ConversationSession, ConversationTurn
    from app.domains.users.models import User


class TurnAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "turn_analyses"

    turn_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_turns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_quality_score: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    communicative_success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_suspicious_transcript: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    strengths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    context_notes: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    analyzer_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), default="conversation.analysis.v1", nullable=False)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    turn: Mapped["ConversationTurn"] = relationship("ConversationTurn")
    session: Mapped["ConversationSession"] = relationship("ConversationSession")
    corrections: Mapped[list["AnalysisCorrection"]] = relationship(
        "AnalysisCorrection",
        back_populates="turn_analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    grammar_notes: Mapped[list["GrammarNote"]] = relationship(
        "GrammarNote",
        back_populates="turn_analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    vocabulary_notes: Mapped[list["VocabularyNote"]] = relationship(
        "VocabularyNote",
        back_populates="turn_analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AnalysisCorrection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_corrections"

    turn_analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("turn_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False)  # MUST_FIX, SHOULD_FIX, NATIVE_ALTERNATIVE, IGNORE
    severity_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    original: Mapped[str] = mapped_column(Text, nullable=False)
    corrected: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    native_alternative: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptable_alternatives: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    context_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), default="high", nullable=False)

    # Relationships
    turn_analysis: Mapped["TurnAnalysis"] = relationship("TurnAnalysis", back_populates="corrections")
    feedbacks: Mapped[list["AnalysisUserFeedback"]] = relationship(
        "AnalysisUserFeedback",
        back_populates="correction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GrammarNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "grammar_notes"

    turn_analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("turn_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    grammar_pattern: Mapped[str] = mapped_column(String(100), nullable=False)
    user_usage: Mapped[str] = mapped_column(Text, nullable=False)
    correct_usage: Mapped[str] = mapped_column(Text, nullable=False)
    short_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)

    turn_analysis: Mapped["TurnAnalysis"] = relationship("TurnAnalysis", back_populates="grammar_notes")


class VocabularyNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vocabulary_notes"

    turn_analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("turn_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_word: Mapped[str] = mapped_column(String(100), nullable=False)
    suggested_alternatives: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    nuance_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    jlpt_level: Mapped[str | None] = mapped_column(String(10), nullable=True)

    turn_analysis: Mapped["TurnAnalysis"] = relationship("TurnAnalysis", back_populates="vocabulary_notes")


class SessionAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "session_analyses"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, default=75, nullable=False)
    strengths: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    repeated_issues: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    top_recommendations: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    total_user_turns_analyzed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_corrections_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    must_fix_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    should_fix_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    native_alt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    grammar_summary: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    vocabulary_summary: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    analyzer_version: Mapped[str] = mapped_column(String(30), default="1.0.0", nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), default="session.analysis.v1", nullable=False)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    session: Mapped["ConversationSession"] = relationship("ConversationSession")


class AnalysisJob(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_jobs"

    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'turn_analysis', 'session_analysis'
    status: Mapped[str] = mapped_column(String(30), default="queued", nullable=False, index=True)
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
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AnalysisUserFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_user_feedback"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
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
    rating: Mapped[str] = mapped_column(String(30), nullable=False)  # helpful, not_helpful, wrong_correction
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    correction: Mapped["AnalysisCorrection | None"] = relationship("AnalysisCorrection", back_populates="feedbacks")
