from typing import Any
from pydantic import BaseModel, Field
from app.domains.audio.contracts import (
    AudioQualityReport,
    AudioQualityStatus,
    PlaybackPreset,
    ProviderHealth,
    VoiceCapability,
    VoiceProfileDTO,
)


class VoiceProfileCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = "voicevox"
    voice_id: str
    description: str | None = None
    settings_json: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False
    is_favorite: bool = False


class VoiceProfileUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    settings_json: dict[str, Any] | None = None
    is_default: bool | None = None
    is_favorite: bool | None = None


class VoiceProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    provider: str
    voice_id: str
    description: str | None = None
    settings_json: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False
    is_favorite: bool = False
    created_at: str
    updated_at: str


class AudioPresetCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    loop_count: int = Field(default=1, ge=1, le=10)
    pause_after_ms: int = Field(default=0, ge=0, le=5000)
    auto_play: bool = True
    record_after: bool = False


class AudioPresetResponse(BaseModel):
    id: str
    user_id: str | None = None
    name: str
    description: str | None = None
    speed: float
    volume: float
    loop_count: int
    pause_after_ms: int
    auto_play: bool
    record_after: bool
    is_system: bool
    created_at: str


class TTSPreviewRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    provider: str = "voicevox"
    voice_id: str = "1"
    speed: float = 1.0
    pitch: float = 0.0
    style: str | None = None


class TTSPreviewResponse(BaseModel):
    audio_base64: str
    format: str = "wav"
    duration_ms: int | None = None
    provider: str
    voice_id: str
    processing_time_ms: int | None = None
    is_cached: bool = False


class AudioQualityCheckRequest(BaseModel):
    audio_base64: str


class AudioSettingsDTO(BaseModel):
    default_tts_provider: str = "voicevox"
    default_stt_provider: str = "faster_whisper"
    default_voice_profile_id: str | None = None
    default_tts_speed: float = 1.0
    default_tts_pitch: float = 0.0
    tts_fallback_enabled: bool = True
    tts_fallback_provider: str = "voicevox"
    tts_fallback_voice_id: str = "1"
    auto_play_ai_response: bool = True
    auto_play_references: bool = True
    voicevox_engine_url: str = "http://127.0.0.1:50021"
    voicevox_engine_path: str = "E:\\VoiceVox"


class VoicevoxEngineDTO(BaseModel):
    url: str
    path: str
    path_exists: bool
    run_exe_path: str
    run_exe_exists: bool
    is_available: bool
    status_message: str
    latency_ms: int | None = None
    available_voices_count: int = 0


class AudioSettingsUpdateRequest(BaseModel):
    default_tts_provider: str | None = None
    default_stt_provider: str | None = None
    default_voice_profile_id: str | None = None
    default_tts_speed: float | None = None
    default_tts_pitch: float | None = None
    tts_fallback_enabled: bool | None = None
    tts_fallback_provider: str | None = None
    tts_fallback_voice_id: str | None = None
    auto_play_ai_response: bool | None = None
    auto_play_references: bool | None = None
    voicevox_engine_url: str | None = None
    voicevox_engine_path: str | None = None
