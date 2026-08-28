import re
from typing import Any

from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.shadowing.contracts import DifficultyReport, SpeakingDifficulty, TranscriptSegmentDTO


class DifficultyAnalyzer:
    """
    Multidimensional speaking difficulty evaluator for Japanese audio segments and videos.
    Combines speech rate (mora/sec), lexical complexity, grammar density, and naturalness.
    """

    _KANJI_RE = re.compile(r"[\u4E00-\u9FFF]")
    _COLLOQUIAL_RE = re.compile(r"(ちゃう|じゃん|っけ|よね|マジ|やばい|ってば|んだ|とく|なきゃ)")
    _FORMAL_KEIGO_RE = re.compile(r"(ございます|いらっしゃ|おっしゃ|申し上げ|いたします|存じ|賜り)")

    @classmethod
    def analyze_segment_difficulty(
        cls,
        text: str,
        duration_seconds: float,
        reading: str | None = None,
    ) -> DifficultyReport:
        """Calculates multi-dimensional difficulty report for a single segment."""
        clean_text = text.strip()
        dur = max(0.4, duration_seconds)

        # 1. Resolve reading and calculate mora rate
        hira = reading or JapaneseReadingResolver.to_hiragana(clean_text)
        # Approximate mora count by length of clean hiragana without small tsu / small vowels
        mora_count = max(1, len(re.sub(r"[ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ]", "", hira)))
        mora_rate = round(mora_count / dur, 2)

        # 2. Lexical complexity (kanji density)
        kanji_count = len(cls._KANJI_RE.findall(clean_text))
        total_chars = max(1, len(clean_text))
        kanji_ratio = kanji_count / total_chars
        lexical_score = min(1.0, kanji_ratio * 1.8)

        # 3. Grammar complexity & keigo detection
        has_keigo = bool(cls._FORMAL_KEIGO_RE.search(clean_text))
        grammar_score = 0.7 if has_keigo else (0.5 if kanji_count > 6 else 0.35)

        # 4. Context naturalness & colloquiality
        has_colloquial = bool(cls._COLLOQUIAL_RE.search(clean_text))
        naturalness_score = 0.85 if has_colloquial else 0.60

        # 5. Sentence density
        density = min(1.0, total_chars / (dur * 8.0))

        # 6. Overall difficulty determination
        reasons: list[str] = []
        if mora_rate >= 7.8:
            reasons.append(f"Tốc độ nói bản xứ rất nhanh ({mora_rate} mora/s)")
        elif mora_rate <= 4.8:
            reasons.append(f"Tốc độ nói chậm rãi, rõ ràng ({mora_rate} mora/s)")
        else:
            reasons.append(f"Tốc độ nói hội thoại tự nhiên ({mora_rate} mora/s)")

        if has_keigo:
            reasons.append("Chứa kính ngữ và mẫu câu trang trọng trong môi trường công việc")
        elif has_colloquial:
            reasons.append("Chứa từ ngữ và đuôi câu khẩu ngữ đời thường")

        if kanji_ratio > 0.45:
            reasons.append("Mật độ từ vựng Hán tự và thuật ngữ tương đối cao")

        # Synthesize overall category
        difficulty_score = (mora_rate / 9.0) * 0.45 + (lexical_score * 0.25) + (grammar_score * 0.20) + (density * 0.10)
        if difficulty_score >= 0.75 or mora_rate >= 8.2:
            overall = SpeakingDifficulty.VERY_HARD
        elif difficulty_score >= 0.58 or mora_rate >= 6.8:
            overall = SpeakingDifficulty.HARD
        elif difficulty_score <= 0.38 and mora_rate <= 5.2:
            overall = SpeakingDifficulty.EASY
        else:
            overall = SpeakingDifficulty.NORMAL

        return DifficultyReport(
            lexical_score=round(lexical_score, 2),
            grammar_score=round(grammar_score, 2),
            speed_mora_per_sec=mora_rate,
            pronunciation_complexity=round(min(1.0, mora_rate / 8.0), 2),
            sentence_density=round(density, 2),
            context_naturalness=round(naturalness_score, 2),
            overall_difficulty=overall,
            reasons=reasons,
        )

    @classmethod
    def aggregate_video_difficulty(
        cls,
        segments: list[TranscriptSegmentDTO],
    ) -> tuple[SpeakingDifficulty, dict[str, Any]]:
        """Computes aggregate difficulty and speed statistics across the full video."""
        if not segments:
            return SpeakingDifficulty.NORMAL, {"avg_mora_rate": 6.0, "total_segments": 0}

        rates = [s.difficulty.speed_mora_per_sec for s in segments if s.difficulty]
        avg_rate = sum(rates) / max(1, len(rates)) if rates else 6.0

        hard_count = sum(1 for s in segments if s.difficulty and s.difficulty.overall_difficulty in (SpeakingDifficulty.HARD, SpeakingDifficulty.VERY_HARD))
        easy_count = sum(1 for s in segments if s.difficulty and s.difficulty.overall_difficulty == SpeakingDifficulty.EASY)

        if hard_count >= len(segments) * 0.45 or avg_rate >= 7.2:
            video_diff = SpeakingDifficulty.HARD
        elif easy_count >= len(segments) * 0.50 and avg_rate <= 5.2:
            video_diff = SpeakingDifficulty.EASY
        else:
            video_diff = SpeakingDifficulty.NORMAL

        summary = {
            "avg_mora_rate": round(avg_rate, 2),
            "total_segments": len(segments),
            "hard_segments_ratio": round(hard_count / max(1, len(segments)), 2),
            "easy_segments_ratio": round(easy_count / max(1, len(segments)), 2),
        }
        return video_diff, summary
