from typing import Any
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class VoiceProfileModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-saved or custom voice profile configuration."""
    __tablename__ = "voice_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="voicevox", nullable=False)
    voice_id: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Voice parameters JSON: speed, pitch, style, volume, etc.
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AudioPresetModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-saved or system playback preset."""
    __tablename__ = "audio_presets"

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    speed: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    volume: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    loop_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    pause_after_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    auto_play: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    record_after: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
