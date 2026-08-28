from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.domains.users.models import User


class UserSettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    theme: Mapped[str] = mapped_column(String(20), default="system", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="ja", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Tokyo", nullable=False)

    default_ai_provider: Mapped[str] = mapped_column(String(50), default="gemini", nullable=False)
    default_ai_model: Mapped[str] = mapped_column(String(100), default="gemini-1.5-flash", nullable=False)
    default_tts_provider: Mapped[str] = mapped_column(String(50), default="voicevox", nullable=False)
    default_stt_provider: Mapped[str] = mapped_column(String(50), default="whisper_local", nullable=False)

    # Phase 2 Routing Configurations
    routing_mode: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)  # 'auto' | 'manual'
    fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fallback_priority: Mapped[str] = mapped_column(String(255), default="gemini,groq,openrouter", nullable=False)

    # Phase 9 Audio Experience Configurations
    default_voice_profile_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    default_tts_speed: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    default_tts_pitch: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tts_fallback_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tts_fallback_provider: Mapped[str] = mapped_column(String(50), default="voicevox", nullable=False)
    tts_fallback_voice_id: Mapped[str] = mapped_column(String(50), default="1", nullable=False)
    auto_play_ai_response: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_play_references: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # VOICEVOX engine customization (user-editable path + URL)
    voicevox_engine_url: Mapped[str] = mapped_column(String(255), default="http://127.0.0.1:50021", nullable=False)
    voicevox_engine_path: Mapped[str] = mapped_column(String(500), default="E:\\VoiceVox", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="settings")

