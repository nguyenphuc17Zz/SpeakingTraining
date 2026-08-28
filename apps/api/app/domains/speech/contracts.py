from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class STTDevice(str, Enum):
    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class STTComputeType(str, Enum):
    AUTO = "auto"
    INT8 = "int8"
    FLOAT16 = "float16"
    FLOAT32 = "float32"


class WordTimestamp(BaseModel):
    word: str
    start_ms: int
    end_ms: int
    confidence: float | None = None


class STTOptions(BaseModel):
    language: str = "ja"
    model: str = "base"
    device: STTDevice = STTDevice.AUTO
    compute_type: STTComputeType = STTComputeType.AUTO
    beam_size: int = 5
    temperature: float = 0.0
    vad_filter: bool = True
    initial_prompt: str | None = None


class STTResult(BaseModel):
    text: str
    language: str = "ja"
    duration_ms: int | None = None
    confidence: float | None = None
    processing_time_ms: int | None = None
    model: str | None = None
    provider: str
    words: list[WordTimestamp] = []
    metadata: dict[str, Any] = Field(default_factory=dict)


class STTProvider(Protocol):
    """Protocol for Speech-to-Text engines (Faster-Whisper, Cloud, etc.)."""

    provider_id: str

    async def transcribe(self, audio_bytes: bytes, options: STTOptions | None = None) -> STTResult:
        ...


class TTSVoice(BaseModel):
    id: str
    name: str
    speaker_id: int | str
    gender: str = "female"
    style: str | None = "Normal"
    preview_url: str | None = None
    capabilities: list[str] = Field(
        default_factory=lambda: ["speed_control", "pitch_control", "volume_control"]
    )


class TTSOptions(BaseModel):
    voice_id: str = "1"
    speaker_id: int = 1
    pitch: float = 0.0  # VOICEVOX pitch default is 0.0
    speed: float = 1.0  # VOICEVOX speed default is 1.0
    volume: float = 1.0
    style: str | None = None
    format: str = "wav"


class TTSAudioOutput(BaseModel):
    audio_bytes: bytes
    format: str = "wav"  # 'wav' or 'mp3'
    duration_ms: int | None = None
    sample_rate: int = 24000
    voice: str
    provider: str
    model: str | None = None
    processing_time_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TTSProvider(Protocol):
    """Protocol for Text-to-Speech engines (VOICEVOX, Gemini TTS, etc.)."""

    provider_id: str

    async def synthesize(self, text: str, options: TTSOptions | None = None) -> TTSAudioOutput:
        ...

    async def get_available_voices(self) -> list[TTSVoice]:
        ...

    async def health_check(self) -> dict[str, Any]:
        ...
