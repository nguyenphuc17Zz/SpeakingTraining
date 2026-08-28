from app.core.config import get_settings
from app.domains.speech.adapters.voicevox import VoicevoxAdapter
from app.domains.speech.contracts import TTSAudioOutput, TTSOptions, TTSProvider, TTSVoice
from app.domains.speech.errors import TTSProviderError

settings = get_settings()


class TTSRouter:
    """Intelligent Text-to-Speech Router for local and remote voice engines."""

    def __init__(self):
        engine_url = getattr(settings, "VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")
        self._providers: dict[str, TTSProvider] = {
            "voicevox": VoicevoxAdapter(engine_url=engine_url),
        }
        self.default_provider_id = "voicevox"

    def register_provider(self, provider_id: str, provider: TTSProvider) -> None:
        self._providers[provider_id] = provider

    def get_provider(self, provider_id: str | None = None) -> TTSProvider:
        target = (provider_id or self.default_provider_id).lower()
        if target not in self._providers:
            raise TTSProviderError(
                message=f"TTS Provider '{target}' is not registered. Available: {list(self._providers.keys())}",
                provider_id=target,
            )
        return self._providers[target]

    async def synthesize(
        self,
        text: str,
        provider_id: str | None = None,
        options: TTSOptions | None = None,
    ) -> TTSAudioOutput:
        """Route text synthesis to the selected or default TTS provider."""
        provider = self.get_provider(provider_id)
        return await provider.synthesize(text, options)

    async def get_available_voices(self, provider_id: str | None = None) -> list[TTSVoice]:
        """Fetch available voices from the specified provider."""
        provider = self.get_provider(provider_id)
        return await provider.get_available_voices()


# Singleton instance
tts_router = TTSRouter()
