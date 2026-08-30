from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.personas.models import Persona
    from app.domains.users.models import User


class ConversationSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_sessions"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    persona_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(String(20), default="conversation", nullable=False)  # 'conversation', 'coaching'
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # 'active', 'completed', 'cancelled', 'error'

    # Session Config Snapshot (Persists settings used at start of session)
    provider_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stt_provider_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stt_model_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tts_provider_preference: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tts_voice_preference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversation_sessions")
    persona: Mapped["Persona"] = relationship("Persona", back_populates="conversation_sessions")
    turns: Mapped[list["ConversationTurn"]] = relationship(
        "ConversationTurn",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.sequence",
        lazy="selectin",
    )


class ConversationTurn(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_turns"

    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    speaker: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' | 'assistant'
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    client_turn_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Telemetry & Providers snapshot
    stt_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stt_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tts_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tts_voice: Mapped[str | None] = mapped_column(String(100), nullable=True)

    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    feedback_hint: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    session: Mapped["ConversationSession"] = relationship("ConversationSession", back_populates="turns")

    @property
    def scaffolding(self) -> dict[str, Any] | None:
        if self.metrics and isinstance(self.metrics, dict):
            return self.metrics.get("scaffolding")
        return None
