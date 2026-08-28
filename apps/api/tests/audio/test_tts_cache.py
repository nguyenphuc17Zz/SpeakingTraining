import time
import pytest
from app.domains.audio.cache import InMemoryTTSCache, TTSCacheKey
from app.domains.audio.contracts import TTSResult


def test_tts_cache_key_generation():
    k1 = TTSCacheKey.create("  こんにちは   世界  ", "voicevox", "1", speed=1.0)
    k2 = TTSCacheKey.create("こんにちは 世界", "VOICEVOX", "1", speed=1.00)
    assert k1.to_hash() == k2.to_hash()

    # Different speed gives different hash
    k3 = TTSCacheKey.create("こんにちは 世界", "voicevox", "1", speed=0.9)
    assert k1.to_hash() != k3.to_hash()

    # Different voice gives different hash
    k4 = TTSCacheKey.create("こんにちは 世界", "voicevox", "2", speed=1.0)
    assert k1.to_hash() != k4.to_hash()


def test_tts_cache_lru_and_ttl():
    cache = InMemoryTTSCache(max_entries=2, default_ttl_seconds=1.0)
    dummy_res = TTSResult(
        audio_bytes=b"dummy_wav_1",
        audio_base64="ZHVtbXlfd2F2XzE=",
        format="wav",
        duration_ms=1000,
        provider="voicevox",
        voice_id="1",
    )

    k1 = TTSCacheKey.create("text1", "voicevox", "1")
    k2 = TTSCacheKey.create("text2", "voicevox", "1")
    k3 = TTSCacheKey.create("text3", "voicevox", "1")

    cache.put(k1, dummy_res)
    cache.put(k2, dummy_res)
    assert cache.size() == 2

    # Access k1 to make k2 oldest
    assert cache.get(k1) is not None

    # Insert k3 -> evicts k2
    cache.put(k3, dummy_res)
    assert cache.size() == 2
    assert cache.get(k1) is not None
    assert cache.get(k2) is None  # evicted!
    assert cache.get(k3) is not None

    # Test TTL expiration
    time.sleep(1.1)
    assert cache.get(k1) is None
    cache.cleanup_expired()
    assert cache.size() == 0
