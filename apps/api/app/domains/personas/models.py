from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.conversation.models import ConversationSession
    from app.domains.users.models import User


class Persona(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "personas"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'Senpai', 'Teacher', 'Friend', 'Interviewer'
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    speaking_style: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'Polite Keigo', 'Casual Tameguchi', 'Encouraging'
    difficulty: Mapped[str] = mapped_column(String(20), default="N3", nullable=False)  # 'N5', 'N4', 'N3', 'N2', 'N1'
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    preferences: Mapped[list["UserPersonaPreference"]] = relationship(
        "UserPersonaPreference",
        back_populates="persona",
        cascade="all, delete-orphan",
    )
    conversation_sessions: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession",
        back_populates="persona",
        cascade="all, delete-orphan",
    )


class UserPersonaPreference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_persona_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "persona_id", name="uq_user_persona_pref"),
    )

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
    custom_prompt_addon: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_pitch: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    voice_speed: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="persona_preferences")
    persona: Mapped["Persona"] = relationship("Persona", back_populates="preferences")
