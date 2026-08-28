from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class VoiceCapability(str, Enum):
    SPEED_CONTROL = "speed_control"
    PITCH_CONTROL = "pitch_control"
    STYLE_CONTROL = "style_control"
    STREAMING = "streaming"
    VOLUME_CONTROL = "volume_control"


class VoiceStyle(str, Enum):
    NORMAL = "normal"
    CASUAL = "casual"
    POLITE = "polite"
    TEACHER = "teacher"
    ENERGETIC = "energetic"
    CALM = "calm"
    PROFESSIONAL = "professional"
    DRAMATIC = "dramatic"


class AudioQualityStatus(str, Enum):
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NOISY = "noisy"
    CLIPPING = "clipping"
    TOO_QUIET = "too_quiet"
    SILENT = "silent"


class PlaybackState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"


class RecordingState(str, Enum):
    IDLE = "idle"
    REQUESTING_PERMISSION = "requesting_permission"
    READY = "ready"
    RECORDING = "recording"
    STOPPING = "stopping"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class TTSState(str, Enum):
    IDLE = "idle"
    GENERATING = "generating"
    READY = "ready"
    PLAYING = "playing"
    COMPLETED = "completed"
    ERROR = "error"


class AudioErrorCode(str, Enum):
    MIC_PERMISSION_DENIED = "MIC_PERMISSION_DENIED"
    DEVICE_UNAVAILABLE = "DEVICE_UNAVAILABLE"
    RECORDING_ERROR = "RECORDING_ERROR"
    TTS_PROVIDER_ERROR = "TTS_PROVIDER_ERROR"
    TTS_VOICE_UNAVAILABLE = "TTS_VOICE_UNAVAILABLE"
    AUDIO_DECODE_ERROR = "AUDIO_DECODE_ERROR"
    PLAYBACK_ERROR = "PLAYBACK_ERROR"
    REFERENCE_AUDIO_ERROR = "REFERENCE_AUDIO_ERROR"
    AUDIO_QUALITY_LOW = "AUDIO_QUALITY_LOW"


class VoiceProfileDTO(BaseModel):
    id: str
    provider: str
    voice_id: str
    name: str
    display_name: str
    language: str = "ja"
    gender: str | None = None  # None if provider does not supply
    default_speed: float = 1.0
    default_pitch: float = 0.0
    style: str | None = "normal"
    capabilities: list[VoiceCapability] = Field(default_factory=list)
    provider_metadata: dict[str, Any] = Field(default_factory=dict)
    is_favorite: bool = False
    is_system: bool = True


class TTSRequest(BaseModel):
    text: str
    provider: str = "voicevox"
    voice_id: str = "1"
    language: str = "ja"
    speed: float = 1.0
    pitch: float = 0.0
    style: str | None = None
    format: str = "wav"
    sample_rate: int = 24000
    user_id: str | None = None
    allow_fallback: bool = True


class TTSResult(BaseModel):
    audio_bytes: bytes
    audio_base64: str | None = None
    format: str = "wav"
    duration_ms: int | None = None
    sample_rate: int = 24000
    provider: str
    voice_id: str
    model: str | None = None
    processing_time_ms: int | None = None
    is_cached: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlaybackPreset(BaseModel):
    id: str
    name: str
    description: str | None = None
    speed: float = 1.0
    volume: float = 1.0
    loop: bool = False
    loop_count: int = 1
    pause_after_ms: int = 0
    auto_play: bool = True
    record_after: bool = False
    is_system: bool = True


class AudioQualityReport(BaseModel):
    volume_rms: float
    volume_db: float
    noise_level_db: float
    snr_db: float | None = None
    has_clipping: bool = False
    clipping_samples_count: int = 0
    duration_ms: int
    quality: AudioQualityStatus
    recommendation: str
    warnings: list[str] = Field(default_factory=list)


class ProviderHealth(BaseModel):
    provider_id: str
    name: str
    is_available: bool
    status_message: str
    checked_at: str
    latency_ms: int | None = None
    available_voices_count: int = 0
