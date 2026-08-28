from typing import Any

from app.core.config import get_settings
from app.domains.speech.adapters.faster_whisper import FasterWhisperAdapter
from app.domains.speech.contracts import STTOptions, STTProvider, STTResult
from app.domains.speech.errors import STTProviderError

settings = get_settings()


class STTRouter:
    """Intelligent Speech-to-Text Router for local and remote STT backends."""

    def __init__(self):
        self._providers: dict[str, STTProvider] = {
            "faster_whisper": FasterWhisperAdapter(
                default_model=getattr(settings, "WHISPER_DEFAULT_MODEL", "base"),
                default_device=getattr(settings, "WHISPER_DEVICE", "auto"),
                default_compute_type=getattr(settings, "WHISPER_COMPUTE_TYPE", "auto"),
            ),
        }
        self.default_provider_id = "faster_whisper"

    def register_provider(self, provider_id: str, provider: STTProvider) -> None:
        self._providers[provider_id] = provider

    def get_provider(self, provider_id: str | None = None) -> STTProvider:
        target = (provider_id or self.default_provider_id).lower()
        if target not in self._providers:
            raise STTProviderError(
                message=f"STT Provider '{target}' is not registered. Available: {list(self._providers.keys())}",
                provider_id=target,
            )
        return self._providers[target]

    async def transcribe(
        self,
        audio_bytes: bytes,
        provider_id: str | None = None,
        options: STTOptions | None = None,
    ) -> STTResult:
        """Route audio transcription to the selected or default STT provider."""
        provider = self.get_provider(provider_id)
        return await provider.transcribe(audio_bytes, options)

    def get_available_models(self, active_model: str = "base") -> list[dict[str, Any]]:
        """List standard Whisper models, download statuses, and hardware recommendations."""
        from app.domains.speech.model_manager import whisper_model_manager
        return whisper_model_manager.get_available_models_info(active_model)


# Singleton instance
stt_router = STTRouter()
