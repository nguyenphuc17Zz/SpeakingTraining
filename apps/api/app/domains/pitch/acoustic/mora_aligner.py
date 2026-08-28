"""MoraAligner — WhisperX forced-align per mora, fallback proportional.

Reuses AlignmentEngine proportional weights when WhisperX not available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.logging import logger
from app.domains.pronunciation.infrastructure.alignment_engine import AlignmentEngine
from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer


@dataclass
class MoraBoundary:
    kana: str
    start_ms: float
    end_ms: float
    duration_ms: float
    is_estimated: bool


class MoraAligner:
    def __init__(self):
        self._base_engine = AlignmentEngine()
        self._mora_analyzer = JapaneseMoraAnalyzer()
        self._whisperx_available = False
        try:
            import whisperx  # type: ignore

            self._whisperx_available = True
        except Exception:
            pass

    def align(
        self,
        text: str,
        speech_start_ms: float,
        speech_end_ms: float,
        word_timestamps: list[dict[str, Any]] | None = None,
        sr: int = 16000,
        samples=None,
    ) -> list[MoraBoundary]:
        # Try WhisperX if samples provided and available
        if self._whisperx_available and samples is not None and word_timestamps is None:
            try:
                # Placeholder: WhisperX would need audio + text; for MVP we fallback
                # Actual WhisperX integration requires model loading; skip for now
                pass
            except Exception as e:
                logger.warning(f"[MoraAligner] WhisperX failed {e}")

        # Fallback: use AlignmentEngine proportional
        # Reuse existing logic to get MoraUnit list, then convert to boundaries
        # We call base engine's align to get expected durations, then map to boundaries
        try:
            # Get mora segmentation
            from app.domains.japanese.provider import get_language_provider

            lang = get_language_provider()
            reading = lang.get_reading(text) or text
            moras = self._mora_analyzer.segment_moras(reading)
            total_moras = len(moras) if moras else 1
            duration_ms = max(1, speech_end_ms - speech_start_ms)
            # Use base engine weights
            # Approximate per-mora weight
            boundaries: list[MoraBoundary] = []
            cur = speech_start_ms
            for mora in moras:
                # Weight via base engine
                # Access private _get_mora_weight via instance
                try:
                    w = self._base_engine._get_mora_weight(mora)  # type: ignore
                except Exception:
                    w = 1.0
                # Distribute proportionally: sum weights = total_weight, each gets w/total * duration
                # For simplicity, equal distribution weighted
                # Compute total weight first
                total_w = sum(self._base_engine._get_mora_weight(m) for m in moras)  # type: ignore
                dur = duration_ms * (w / total_w) if total_w else duration_ms / total_moras
                boundaries.append(MoraBoundary(kana=mora.kana, start_ms=cur, end_ms=cur + dur, duration_ms=dur, is_estimated=True))
                cur += dur
            return boundaries
        except Exception as e:
            logger.warning(f"[MoraAligner] fallback failed {e}")
            # Ultimate fallback: equal split
            moras = self._mora_analyzer.segment_moras(text)
            if not moras:
                return [MoraBoundary(kana=text, start_ms=speech_start_ms, end_ms=speech_end_ms, duration_ms=speech_end_ms - speech_start_ms, is_estimated=True)]
            dur_each = (speech_end_ms - speech_start_ms) / len(moras)
            cur = speech_start_ms
            out = []
            for m in moras:
                out.append(MoraBoundary(kana=m.kana, start_ms=cur, end_ms=cur + dur_each, duration_ms=dur_each, is_estimated=True))
                cur += dur_each
            return out
