from dataclasses import dataclass
import hashlib
import time
from collections import OrderedDict
from typing import Any
from app.domains.audio.contracts import TTSResult


@dataclass(frozen=True)
class TTSCacheKey:
    normalized_text: str
    provider: str
    voice_id: str
    speed: float
    pitch: float
    style: str | None
    audio_format: str
    user_id: str | None = None
    version: str = "v1"

    @classmethod
    def create(
        cls,
        text: str,
        provider: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 0.0,
        style: str | None = None,
        audio_format: str = "wav",
        user_id: str | None = None,
    ) -> "TTSCacheKey":
        normalized = " ".join(text.strip().split())
        return cls(
            normalized_text=normalized,
            provider=provider.lower(),
            voice_id=str(voice_id),
            speed=round(speed, 2),
            pitch=round(pitch, 2),
            style=style.lower() if style else None,
            audio_format=audio_format.lower(),
            user_id=user_id,
        )

    def to_hash(self) -> str:
        payload = f"{self.user_id}:{self.provider}:{self.voice_id}:{self.speed}:{self.pitch}:{self.style}:{self.audio_format}:{self.version}:{self.normalized_text}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class InMemoryTTSCache:
    """
    High-performance LRU + TTL in-memory cache for synthesized Japanese TTS audio.
    Avoids redundant expensive syntheses of common sentences and phrases.
    """

    def __init__(self, max_entries: int = 500, default_ttl_seconds: float = 7200.0):
        self.max_entries = max_entries
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, tuple[TTSResult, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: TTSCacheKey) -> TTSResult | None:
        cache_id = key.to_hash()
        if cache_id not in self._cache:
            self._misses += 1
            return None

        result, expires_at = self._cache[cache_id]
        if time.time() > expires_at:
            del self._cache[cache_id]
            self._misses += 1
            return None

        # Move to end for LRU
        self._cache.move_to_end(cache_id)
        self._hits += 1

        # Return a copy marked as cached
        return result.model_copy(update={"is_cached": True})

    def put(self, key: TTSCacheKey, result: TTSResult, ttl_seconds: float | None = None) -> None:
        cache_id = key.to_hash()
        expires_at = time.time() + (ttl_seconds or self.default_ttl_seconds)

        if cache_id in self._cache:
            self._cache.move_to_end(cache_id)
        self._cache[cache_id] = (result, expires_at)

        # Evict oldest if exceeding capacity
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)

    def cleanup_expired(self) -> int:
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now > exp]
        for k in expired_keys:
            del self._cache[k]
        return len(expired_keys)

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def size(self) -> int:
        return len(self._cache)

    def get_stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = (self._hits / total) if total > 0 else 0.0
        total_audio_bytes = sum(len(res.audio_bytes or b"") for res, _ in self._cache.values())

        return {
            "entries": len(self._cache),
            "max_entries": self.max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 3),
            "approx_audio_bytes": total_audio_bytes,
            "ttl_seconds": self.default_ttl_seconds,
        }


# Global singleton TTS cache with 500 entries capacity and 2h TTL
tts_cache = InMemoryTTSCache(max_entries=500, default_ttl_seconds=7200.0)
