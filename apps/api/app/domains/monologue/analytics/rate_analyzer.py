"""SpeechRateAnalyzer §17 — Japanese-relevant units."""

from __future__ import annotations

import re


class SpeechRateAnalyzer:
    @staticmethod
    def analyze(
        transcript: str,
        speech_duration_ms: int,
        mora_count: int | None,
        word_timestamps: list[dict] | None = None,
    ) -> dict:
        if speech_duration_ms < 1000:
            return {
                "chars_per_min": 0,
                "tokens_per_min": 0,
                "mora_per_sec": None,
                "speech_seconds_per_min": None,
                "total_chars": len(re.sub(r"\s", "", transcript)),
                "total_tokens": 0,
                "rate_quality": "too_short",
            }
        total_chars = len(re.sub(r"\s", "", transcript))
        # token count via Japanese-aware regex
        tokens = len(re.findall(r"[ぁ-んァ-ン一-龯]+|\w+", transcript)) or total_chars
        duration_min = speech_duration_ms / 60000
        duration_sec = speech_duration_ms / 1000
        chars_per_min = round(total_chars / duration_min, 1)
        tokens_per_min = round(tokens / duration_min, 1)
        mora_per_sec = round(mora_count / duration_sec, 2) if mora_count else None

        # speech seconds per minute (if word timestamps available)
        speech_seconds_per_min = None
        if word_timestamps:
            speech_ms = sum((w.get("end_ms", 0) - w.get("start_ms", 0)) for w in word_timestamps if w.get("end_ms") and w.get("start_ms"))
            speech_seconds_per_min = round((speech_ms / 1000) / duration_min, 2)

        # evaluation: not faster=better
        # heuristic bands for Japanese monologue @ N3: ~300-450 chars/min or 5-8 mora/sec is natural
        rate_quality = "normal"
        if chars_per_min and chars_per_min < 150:
            rate_quality = "slow"
        elif chars_per_min and chars_per_min > 550:
            rate_quality = "fast"
        if mora_per_sec is not None:
            if mora_per_sec < 4:
                rate_quality = "slow"
            elif mora_per_sec > 9:
                rate_quality = "fast"

        return {
            "chars_per_min": chars_per_min,
            "tokens_per_min": tokens_per_min,
            "mora_per_sec": mora_per_sec,
            "speech_seconds_per_min": speech_seconds_per_min,
            "total_chars": total_chars,
            "total_tokens": tokens,
            "rate_quality": rate_quality,
        }
