import re
from typing import Any

from app.domains.shadowing.contracts import TranscriptQuality, TranscriptQualityReport


class TranscriptQualityEvaluator:
    """Evaluates transcript quality, Japanese language verification, and timestamp validity."""

    # Japanese character ranges: Hiragana (\u3040-\u309F), Katakana (\u30A0-\u30FF), Kanji (\u4E00-\u9FFF)
    _HIRAGANA_RE = re.compile(r"[\u3040-\u309F]")
    _KATAKANA_RE = re.compile(r"[\u30A0-\u30FF]")
    _KANJI_RE = re.compile(r"[\u4E00-\u9FFF]")
    _LATIN_RE = re.compile(r"[a-zA-Z]")

    @classmethod
    def evaluate_transcript(
        cls,
        segments: list[Any],
    ) -> TranscriptQualityReport:
        """
        Validates language, density, and timestamps across all segments.
        """
        if not segments:
            return TranscriptQualityReport(
                quality=TranscriptQuality.LOW,
                language="Unknown",
                has_timestamps=False,
                confidence=0.0,
                issues=["Empty transcript."],
            )

        total_chars = 0
        japanese_chars = 0
        latin_chars = 0
        total_duration = 0.0
        issues: list[str] = []

        for seg in segments:
            text = getattr(seg, "text", "") or seg.get("text", "") if isinstance(seg, dict) else ""
            start_t = getattr(seg, "start_time", 0.0) or seg.get("start", 0.0) if isinstance(seg, dict) else 0.0
            end_t = getattr(seg, "end_time", 0.0) or seg.get("end", 0.0) if isinstance(seg, dict) else 0.0

            dur = max(0.0, end_t - start_t)
            total_duration += dur

            for ch in text:
                total_chars += 1
                if cls._HIRAGANA_RE.match(ch) or cls._KATAKANA_RE.match(ch) or cls._KANJI_RE.match(ch):
                    japanese_chars += 1
                elif cls._LATIN_RE.match(ch):
                    latin_chars += 1

        if total_chars == 0:
            return TranscriptQualityReport(
                quality=TranscriptQuality.LOW,
                language="Unknown",
                has_timestamps=False,
                confidence=0.0,
                issues=["No characters detected in transcript."],
            )

        jp_ratio = japanese_chars / max(1, total_chars)

        # 1. Language validation
        is_japanese = jp_ratio >= 0.25 or (japanese_chars > 20 and jp_ratio >= 0.15)
        if not is_japanese:
            issues.append(f"Source transcript language does not appear to be Japanese (Japanese ratio: {jp_ratio:.1%}).")

        # 2. Timestamp quality check
        has_timestamps = total_duration > 0.5
        if not has_timestamps:
            issues.append("Timestamps are missing or duration is zero.")

        # 3. Quality categorization
        if is_japanese and jp_ratio >= 0.60 and has_timestamps and len(segments) >= 3:
            quality = TranscriptQuality.HIGH
            confidence = 0.95
        elif is_japanese and has_timestamps:
            quality = TranscriptQuality.MEDIUM
            confidence = 0.75
        else:
            quality = TranscriptQuality.LOW
            confidence = 0.35

        return TranscriptQualityReport(
            quality=quality,
            language="Japanese" if is_japanese else "Non-Japanese",
            has_timestamps=has_timestamps,
            confidence=confidence,
            issues=issues,
        )
