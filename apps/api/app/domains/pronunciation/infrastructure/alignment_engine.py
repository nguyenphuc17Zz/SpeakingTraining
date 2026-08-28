from typing import Any
import numpy as np

from app.domains.pronunciation.contracts import (
    AlignmentResult,
    AlignmentSegment,
    AnalysisConfidenceLevel,
    MoraUnit,
)
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer
from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
from app.domains.speech.contracts import WordTimestamp


class AlignmentEngine:
    """Aligns target Japanese mora sequence with speech audio timestamps and VAD segments."""

    @classmethod
    def align(
        cls,
        target_text: str,
        speech_start_ms: int,
        speech_end_ms: int,
        word_timestamps: list[WordTimestamp] | None = None,
        user_transcript: str | None = None,
    ) -> AlignmentResult:
        """
        Performs forced / dynamic alignment of target moras across the utterance time bounds.
        """
        # 1. Target moras
        target_hiragana = JapaneseReadingResolver.to_hiragana(target_text)
        moras = JapaneseMoraAnalyzer.segment_moras(target_hiragana)
        total_moras = len(moras)

        if total_moras == 0:
            return AlignmentResult(
                segments=[],
                mora_units=[],
                confidence_level=AnalysisConfidenceLevel.UNCERTAIN,
                total_speech_duration_ms=0,
            )

        speech_duration_ms = max(100, speech_end_ms - speech_start_ms)

        # 2. Check compatibility between target and user transcript (if provided)
        confidence_level = AnalysisConfidenceLevel.HIGH
        unmatched_regions: list[tuple[int, int]] = []

        if user_transcript:
            user_hiragana = JapaneseReadingResolver.to_hiragana(user_transcript)
            user_mora_count = JapaneseMoraAnalyzer.get_mora_count(user_hiragana)
            diff = abs(total_moras - user_mora_count)
            if diff > max(2, total_moras * 0.4):
                confidence_level = AnalysisConfidenceLevel.LOW
            elif diff > 0:
                confidence_level = AnalysisConfidenceLevel.MEDIUM

        # 3. Utilize WordTimestamps from STT if available and aligned
        if word_timestamps and len(word_timestamps) > 0:
            aligned_moras, segments = cls._align_with_word_timestamps(
                moras=moras,
                word_timestamps=word_timestamps,
                speech_start_ms=speech_start_ms,
                speech_end_ms=speech_end_ms,
            )
        else:
            # Fallback to proportional duration model with Japanese phoneme duration weights
            aligned_moras, segments = cls._align_proportional(
                moras=moras,
                speech_start_ms=speech_start_ms,
                speech_end_ms=speech_end_ms,
            )

        return AlignmentResult(
            segments=segments,
            mora_units=aligned_moras,
            confidence_level=confidence_level,
            unmatched_regions=unmatched_regions,
            total_speech_duration_ms=speech_duration_ms,
        )

    @classmethod
    def _get_mora_weight(cls, mora: MoraUnit) -> float:
        """Returns relative duration weight for different mora categories in Japanese."""
        if mora.kana == "っ":
            return 1.1   # Sokuon pause is full mora or slightly prolonged
        if mora.kana == "ー" or (mora.is_special and mora.special_type == "long_vowel"):
            return 1.05  # Long vowel extension
        if mora.kana == "ん":
            return 0.95  # Hatsuon
        if mora.is_special and mora.special_type == "contracted":
            return 1.05  # Yōon (きゃ, etc.)
        return 1.0       # Standard CV mora

    @classmethod
    def _align_proportional(
        cls,
        moras: list[MoraUnit],
        speech_start_ms: int,
        speech_end_ms: int,
    ) -> tuple[list[MoraUnit], list[AlignmentSegment]]:
        """Distributes utterance duration across moras based on Japanese linguistic duration weights."""
        total_duration_ms = max(100, speech_end_ms - speech_start_ms)
        weights = [cls._get_mora_weight(m) for m in moras]
        total_weight = sum(weights)

        # Baseline expected duration per standard mora at average Japanese speaking tempo (~150-180ms/mora)
        avg_actual_mora_ms = total_duration_ms / float(max(1, len(moras)))

        aligned_moras: list[MoraUnit] = []
        current_time = float(speech_start_ms)

        for i, mora in enumerate(moras):
            w = weights[i]
            mora_dur_ms = int(round((w / total_weight) * total_duration_ms))
            mora_dur_ms = max(40, mora_dur_ms)

            # Expected duration for a neutral speaker at this speed
            expected_ms = int(round(w * avg_actual_mora_ms))

            aligned_m = MoraUnit(
                mora_index=mora.mora_index,
                kana=mora.kana,
                phonemes=mora.phonemes,
                is_special=mora.is_special,
                special_type=mora.special_type,
                expected_duration_ms=expected_ms,
                actual_duration_ms=mora_dur_ms,
                duration_ratio=round(mora_dur_ms / float(max(1, expected_ms)), 2),
                confidence=0.9,
            )
            aligned_moras.append(aligned_m)
            current_time += mora_dur_ms

        segment = AlignmentSegment(
            text="".join([m.kana for m in moras]),
            mora_list=[m.kana for m in moras],
            start_ms=speech_start_ms,
            end_ms=speech_end_ms,
            confidence=0.9,
        )

        return aligned_moras, [segment]

    @classmethod
    def _align_with_word_timestamps(
        cls,
        moras: list[MoraUnit],
        word_timestamps: list[WordTimestamp],
        speech_start_ms: int,
        speech_end_ms: int,
    ) -> tuple[list[MoraUnit], list[AlignmentSegment]]:
        """Sub-segments word-level STT timestamps into mora-level timestamps."""
        # Simple & effective: align each word's moras inside that word's start/end window
        total_speech_ms = max(100, speech_end_ms - speech_start_ms)
        avg_mora_ms = total_speech_ms / float(max(1, len(moras)))

        aligned_moras: list[MoraUnit] = []
        segments: list[AlignmentSegment] = []

        # Map word timestamps to moras sequentially
        mora_idx = 0
        total_moras = len(moras)

        for wt in word_timestamps:
            word_hiragana = JapaneseReadingResolver.to_hiragana(wt.word)
            word_moras = JapaneseMoraAnalyzer.segment_moras(word_hiragana)
            num_w_moras = len(word_moras)

            if num_w_moras == 0 or mora_idx >= total_moras:
                continue

            take_moras = min(num_w_moras, total_moras - mora_idx)
            w_start = max(speech_start_ms, wt.start_ms)
            w_end = min(speech_end_ms, max(w_start + 60, wt.end_ms))
            w_dur = w_end - w_start

            w_weights = [cls._get_mora_weight(moras[mora_idx + k]) for k in range(take_moras)]
            w_tot_weight = sum(w_weights) or 1.0

            for k in range(take_moras):
                m = moras[mora_idx + k]
                m_dur = int(round((w_weights[k] / w_tot_weight) * w_dur))
                m_dur = max(40, m_dur)

                aligned_moras.append(
                    MoraUnit(
                        mora_index=m.mora_index,
                        kana=m.kana,
                        phonemes=m.phonemes,
                        is_special=m.is_special,
                        special_type=m.special_type,
                        expected_duration_ms=int(round(w_weights[k] * avg_mora_ms)),
                        actual_duration_ms=m_dur,
                        duration_ratio=round(m_dur / float(max(1, int(round(w_weights[k] * avg_mora_ms)))), 2),
                        confidence=wt.confidence or 0.85,
                    )
                )

            segments.append(
                AlignmentSegment(
                    text=wt.word,
                    mora_list=[m.kana for m in word_moras],
                    start_ms=w_start,
                    end_ms=w_end,
                    confidence=wt.confidence or 0.85,
                )
            )
            mora_idx += take_moras

        # Fill any trailing moras not covered by word timestamps
        if mora_idx < total_moras:
            remaining = total_moras - mora_idx
            rem_start = aligned_moras[-1].actual_duration_ms if aligned_moras else speech_start_ms
            rem_dur = max(100, speech_end_ms - int(rem_start))
            for k in range(remaining):
                m = moras[mora_idx + k]
                m_dur = int(rem_dur / remaining)
                aligned_moras.append(
                    MoraUnit(
                        mora_index=m.mora_index,
                        kana=m.kana,
                        phonemes=m.phonemes,
                        is_special=m.is_special,
                        special_type=m.special_type,
                        expected_duration_ms=int(round(cls._get_mora_weight(m) * avg_mora_ms)),
                        actual_duration_ms=m_dur,
                        duration_ratio=round(m_dur / float(max(1, avg_mora_ms)), 2),
                        confidence=0.7,
                    )
                )

        return aligned_moras, segments
