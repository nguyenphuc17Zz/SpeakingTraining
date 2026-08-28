import base64
import time
from datetime import datetime, timezone

from app.core.logging import logger
from app.domains.audio.cache import TTSCacheKey, tts_cache
from app.domains.audio.contracts import ProviderHealth, TTSRequest, TTSResult
from app.domains.speech.contracts import TTSOptions
from app.domains.speech.errors import TTSProviderError, TTSUnavailableError
from app.domains.speech.tts_router import tts_router


class TTSService:
    """
    Unified Text-to-Speech service providing caching, fallback policies,
    latency tracking, and standardized audio output contracts.
    """

    def __init__(self):
        self.router = tts_router

    async def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Synthesizes Japanese text into speech with LRU cache and automatic fallback.
        """
        if not request.text or not request.text.strip():
            return TTSResult(
                audio_bytes=b"",
                audio_base64="",
                format=request.format,
                duration_ms=0,
                provider=request.provider,
                voice_id=request.voice_id,
                processing_time_ms=0,
                is_cached=False,
            )

        # 1. Check in-memory cache
        cache_key = TTSCacheKey.create(
            text=request.text,
            provider=request.provider,
            voice_id=request.voice_id,
            speed=request.speed,
            pitch=request.pitch,
            style=request.style,
            audio_format=request.format,
            user_id=request.user_id,
        )

        cached_res = tts_cache.get(cache_key)
        if cached_res is not None:
            return cached_res

        start_time = time.perf_counter()
        options = TTSOptions(
            voice_id=request.voice_id,
            speed=request.speed,
            pitch=request.pitch,
            style=request.style,
            format=request.format,
        )

        try:
            # 2. Attempt synthesis via requested provider
            output = await self.router.synthesize(
                text=request.text,
                provider_id=request.provider,
                options=options,
            )

            audio_b64 = base64.b64encode(output.audio_bytes).decode("ascii")
            proc_ms = int((time.perf_counter() - start_time) * 1000)

            result = TTSResult(
                audio_bytes=output.audio_bytes,
                audio_base64=audio_b64,
                format=output.format,
                duration_ms=output.duration_ms,
                sample_rate=output.sample_rate,
                provider=request.provider,
                voice_id=request.voice_id,
                processing_time_ms=proc_ms,
                is_cached=False,
                metadata=output.metadata,
            )

            # Store in cache
            tts_cache.put(cache_key, result)
            return result

        except (TTSProviderError, TTSUnavailableError) as err:
            logger.warning(
                f"[TTSService] Synthesis failed on provider '{request.provider}': {err}"
            )
            # 3. Fallback logic if enabled
            if request.allow_fallback and request.provider != "voicevox":
                logger.info(f"[TTSService] Falling back to default VOICEVOX provider for '{request.text[:20]}...'")
                fallback_req = request.model_copy(update={"provider": "voicevox", "voice_id": "1", "allow_fallback": False})
                return await self.synthesize(fallback_req)
            raise

    async def preview_voice(
        self,
        text: str,
        voice_id: str,
        provider: str = "voicevox",
        speed: float = 1.0,
        pitch: float = 0.0,
        style: str | None = None,
    ) -> TTSResult:
        """Synthesizes a short preview clip with caching."""
        preview_text = text[:150] if text else "こんにちは。今日も一緒に日本語を練習しましょう。"
        req = TTSRequest(
            text=preview_text,
            provider=provider,
            voice_id=voice_id,
            speed=speed,
            pitch=pitch,
            style=style,
            allow_fallback=False,
        )
        return await self.synthesize(req)

    async def get_providers_health(self) -> list[ProviderHealth]:
        """Checks health and latency of all registered TTS engines."""
        health_list: list[ProviderHealth] = []
        now_str = datetime.now(timezone.utc).isoformat()

        # Check VOICEVOX provider
        try:
            voicevox_provider = self.router.get_provider("voicevox")
            health_dict = await voicevox_provider.health_check()
            health_list.append(
                ProviderHealth(
                    provider_id="voicevox",
                    name="VOICEVOX Engine (Local / Self-hosted)",
                    is_available=health_dict.get("is_available", False),
                    status_message=health_dict.get("status_message", "Unknown status"),
                    checked_at=now_str,
                    latency_ms=health_dict.get("latency_ms"),
                    available_voices_count=health_dict.get("available_voices_count", 0),
                )
            )
        except Exception as e:
            health_list.append(
                ProviderHealth(
                    provider_id="voicevox",
                    name="VOICEVOX Engine",
                    is_available=False,
                    status_message=f"Offline ({str(e)})",
                    checked_at=now_str,
                    available_voices_count=0,
                )
            )

        return health_list


# Global singleton TTSService
tts_service = TTSService()
