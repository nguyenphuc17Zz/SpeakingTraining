from typing import TYPE_CHECKING, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.ai.models import AIUsageRecord
    from app.domains.conversation.models import ConversationSession
    from app.domains.personas.models import UserPersonaPreference
    from app.domains.providers.models import APICredential
    from app.domains.settings.models import UserSettings


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(100), default="Learner", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tokyo", nullable=False)
    locale: Mapped[str] = mapped_column(String(20), default="ja-JP", nullable=False)

    # Relationships
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    credentials: Mapped[list["APICredential"]] = relationship(
        "APICredential",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    persona_preferences: Mapped[list["UserPersonaPreference"]] = relationship(
        "UserPersonaPreference",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    conversation_sessions: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_usages: Mapped[list["AIUsageRecord"]] = relationship(
        "AIUsageRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )

