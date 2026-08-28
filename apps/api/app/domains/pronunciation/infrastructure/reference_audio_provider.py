from typing import Protocol

from app.core.logging import logger
from app.domains.pronunciation.contracts import ReferenceType
from app.domains.speech.contracts import TTSOptions
from app.domains.speech.tts_router import tts_router


class ReferenceAudioProvider(Protocol):
    """Protocol for generating or fetching target reference audio."""

    async def get_reference_audio(
        self, text: str, speaker_id: int | None = None
    ) -> tuple[bytes | None, ReferenceType]:
        ...


class VoicevoxReferenceAudioProvider:
    """Uses VOICEVOX adapter to synthesize reference audio."""

    _CACHE: dict[tuple[str, int], bytes] = {}

    async def get_reference_audio(
        self, text: str, speaker_id: int | None = None
    ) -> tuple[bytes | None, ReferenceType]:
        """Synthesizes or retrieves cached reference audio for target sentence."""
        if not text:
            return None, ReferenceType.UNKNOWN

        resolved_speaker = speaker_id or 1
        cache_key = (text.strip(), resolved_speaker)

        if cache_key in self._CACHE:
            return self._CACHE[cache_key], ReferenceType.SYNTHETIC

        try:
            tts_opts = TTSOptions(voice_id=str(resolved_speaker), speaker_id=resolved_speaker)
            output = await tts_router.synthesize(text=text, provider_id="voicevox", options=tts_opts)
            if output.audio_bytes:
                self._CACHE[cache_key] = output.audio_bytes
                return output.audio_bytes, ReferenceType.SYNTHETIC
        except Exception as e:
            logger.warning(f"[VoicevoxReferenceAudioProvider] Synthesis failed for '{text}': {e}")

        return None, ReferenceType.UNKNOWN
