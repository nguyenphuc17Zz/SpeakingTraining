from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserSettingsBase(BaseModel):
    theme: str = "system"
    language: str = "ja"
    timezone: str = "Asia/Tokyo"
    default_ai_provider: str = "gemini"
    default_ai_model: str = "gemini-1.5-flash"
    default_tts_provider: str = "voicevox"
    default_stt_provider: str = "whisper_local"
    routing_mode: str = "auto"
    fallback_enabled: bool = True
    fallback_priority: str = "gemini,groq,openrouter"
    voicevox_engine_url: str = "http://127.0.0.1:50021"
    voicevox_engine_path: str = "E:\\VoiceVox"


class UserSettingsUpdate(BaseModel):
    theme: str | None = None
    language: str | None = None
    timezone: str | None = None
    default_ai_provider: str | None = None
    default_ai_model: str | None = None
    default_tts_provider: str | None = None
    default_stt_provider: str | None = None
    routing_mode: str | None = None
    fallback_enabled: bool | None = None
    fallback_priority: str | None = None
    voicevox_engine_url: str | None = None
    voicevox_engine_path: str | None = None


class UserSettingsRead(UserSettingsBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

