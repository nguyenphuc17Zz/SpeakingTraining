"""Monologue Audio Analysis Pipeline §15."""

from __future__ import annotations

import re
import time
from typing import Any

from app.domains.monologue.analytics.discourse_analyzer import DiscourseStructureAnalyzer
from app.domains.monologue.analytics.filler_analyzer import FillerAnalyzer
from app.domains.monologue.analytics.idea_density import IdeaDensityAnalyzer
from app.domains.monologue.analytics.lexical_profiler import LexicalProfiler
from app.domains.monologue.analytics.pause_analyzer import PauseAnalyzer
from app.domains.monologue.analytics.quality_gate import SpeechQualityGate
from app.domains.monologue.analytics.rate_analyzer import SpeechRateAnalyzer
from app.domains.monologue.analytics.self_repair_analyzer import SelfRepairAnalyzer
from app.domains.monologue.contracts import SpeechGenre


class MonologuePipeline:
    """Deterministic pipeline: Audio → Quality → VAD/STT → Metrics → Lexical → Discourse."""

    def __init__(self):
        self.filler_analyzer = FillerAnalyzer()
        self.pause_analyzer = PauseAnalyzer()
        self.repair_analyzer = SelfRepairAnalyzer()
        self.lexical_profiler = LexicalProfiler()
        self.discourse_analyzer = DiscourseStructureAnalyzer()

    async def analyze_transcript(
        self,
        transcript: str,
        words: list[dict] | None,
        speech_duration_ms: int,
        target_duration_ms: int,
        stt_confidence: float | None,
        audio_bytes: bytes | None = None,
        genre: str | SpeechGenre = SpeechGenre.OPINION,
        has_clipping: bool = False,
        snr_db: float | None = None,
        is_text_only: bool = False,
    ) -> dict[str, Any]:
        # 1. Quality gate
        quality = SpeechQualityGate.evaluate(
            audio_bytes=audio_bytes,
            speech_duration_ms=speech_duration_ms,
            target_duration_ms=target_duration_ms,
            stt_confidence=stt_confidence,
            word_count=len(words or []),
            has_clipping=has_clipping,
            snr_db=snr_db,
            is_text_only=is_text_only,
        )

        # 2. Filler
        filler_events, filler_summary = self.filler_analyzer.analyze(transcript, words)
        filler_per_min = FillerAnalyzer.fillers_per_minute(len(filler_events), speech_duration_ms)

        # 3. Self-repair — per_min with floor 0.25 (12s) to avoid inflating short samples
        repair_events, repair_summary = self.repair_analyzer.analyze(transcript, words)
        mins = max(0.25, speech_duration_ms / 60000)
        repair_summary["repair_frequency_per_min"] = round(len(repair_events) / mins, 2)

        # 4. Pause (needs filler/repair for context)
        filler_dicts = [{"token": e.token, "start_ms": e.start_ms, "end_ms": e.end_ms} for e in filler_events]
        repair_dicts = [{"type": e.type, "start_ms": e.start_ms} for e in repair_events]
        pause_events, pause_summary = self.pause_analyzer.analyze(words or [], speech_duration_ms, transcript, filler_dicts, repair_dicts)

        # 5. Rate (mora via provider if available) — no char-count fallback (hard error)
        mora_count = None
        try:
            from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer

            ma = JapaneseMoraAnalyzer()
            from app.domains.japanese.provider import get_language_provider

            lang = get_language_provider()
            reading = lang.get_reading(transcript) or transcript
            moras = ma.segment_moras(reading)
            mora_count = len(moras)
        except Exception as e:
            from app.core.logging import logger
            logger.debug(f"[MonologuePipeline] mora count failed: {e}")
            mora_count = None

        rate = SpeechRateAnalyzer.analyze(transcript, speech_duration_ms, mora_count, words)  # type: ignore

        # 6. Idea density
        idea = IdeaDensityAnalyzer.analyze(transcript)

        # 7. Lexical
        lexical = self.lexical_profiler.analyze(transcript)

        # 8. Discourse
        discourse = self.discourse_analyzer.analyze(transcript, genre)
        coherence = DiscourseStructureAnalyzer.coherence_score(
            idea_density=idea,
            discourse=discourse,
            filler_ratio=filler_summary.get("filler_ratio"),
            pause_breakdown=pause_summary.get("breakdown"),
        )

        # 9. Timelines
        fluency_timeline = self._build_fluency_timeline(
            speech_duration_ms, pause_events, filler_events, transcript, words or []
        )
        filler_timeline = [
            {"at_ms": e.start_ms or 0, "token": e.token, "class": e.token_class.value} for e in filler_events
        ] + [
            {"at_ms": e.start_ms or 0, "token": e.type, "class": "self_repair"} for e in repair_events
        ]
        filler_timeline.sort(key=lambda x: x["at_ms"])

        # 10. Assemble deterministic metrics
        metrics = {
            "speech_duration_ms": speech_duration_ms,
            "target_duration_ms": target_duration_ms,
            "chars_per_min": rate["chars_per_min"],
            "tokens_per_min": rate["tokens_per_min"],
            "mora_per_sec": rate["mora_per_sec"],
            "speech_seconds_per_min": rate["speech_seconds_per_min"],
            "total_chars": rate["total_chars"],
            "total_tokens": rate["total_tokens"],
            "mora_count": mora_count,
            "rate_quality": rate["rate_quality"],
            "pause_events": [e.model_dump() if hasattr(e, "model_dump") else e for e in pause_events],
            "pause_summary": pause_summary,
            "filler_events": [e.model_dump() if hasattr(e, "model_dump") else e for e in filler_events],
            "filler_summary": {**filler_summary, "filler_per_min": filler_per_min},
            "repair_events": [e.model_dump() if hasattr(e, "model_dump") else e for e in repair_events],
            "repair_summary": repair_summary,
            "speech_metrics_core": {
                "speech_duration_ms": speech_duration_ms,
                "target_duration_ms": target_duration_ms,
                "total_chars": rate["total_chars"],
                "total_tokens": rate["total_tokens"],
                "mora_count": mora_count,
                "chars_per_min": rate["chars_per_min"],
                "tokens_per_min": rate["tokens_per_min"],
                "mora_per_sec": rate["mora_per_sec"],
                "pause_count": pause_summary["total"],
                "filler_count": len(filler_events),
                "filler_per_min": filler_per_min,
                "filler_ratio": filler_summary.get("filler_ratio", 0),
                "long_pause_count": pause_summary.get("long", 0),
                "stall_count": pause_summary.get("stall", 0),
                "breakdown_count": pause_summary.get("breakdown", 0),
                "self_repair_count": len(repair_events),
                "abandoned_rate": repair_summary.get("abandoned_rate", 0),
                "stt_confidence": stt_confidence,
            },
            "idea_density": idea,
            "lexical_profile": lexical,
            "discourse": discourse,
            "coherence_deterministic": coherence,
            "fluency_timeline": fluency_timeline,
            "filler_timeline": sorted(filler_timeline, key=lambda x: x["at_ms"]),
            "quality_gate": quality.model_dump() if hasattr(quality, "model_dump") else quality,
        }

        return metrics

    @staticmethod
    def _build_fluency_timeline(
        duration_ms: int,
        pause_events: list,
        filler_events: list,
        transcript: str,
        words: list[dict],
    ) -> list[dict]:
        # Split duration into 15s windows (§50)
        if duration_ms <= 0:
            return []
        window_ms = 15000
        windows = []
        for start in range(0, duration_ms, window_ms):
            end = min(start + window_ms, duration_ms)
            # count pauses/fillers in window
            pauses_in = [p for p in pause_events if start <= (p.start_ms or 0) < end]
            fillers_in = [f for f in filler_events if start <= (f.start_ms or 0) < end]
            long_pauses = [p for p in pauses_in if p.pause_class.value in ("long_pause", "stall", "breakdown")]
            breakdowns = [p for p in pauses_in if p.pause_class.value == "breakdown"]
            # also check repetition in window via transcript slice heuristic
            status = "fluent"
            label = "fluent"
            if breakdowns:
                status = "breakdown"
                label = "breakdown"
            elif long_pauses and len(long_pauses) >= 1:
                status = "more_pauses"
                label = "more pauses"
            elif fillers_in and len(fillers_in) >= 3:
                status = "repetition"
                label = "repetition"
            elif len(pauses_in) >= 4:
                status = "more_pauses"
                label = "more pauses"
            color = {"fluent": "🟢", "more_pauses": "🟡", "repetition": "🟠", "breakdown": "🔴"}.get(status, "🟢")
            windows.append({
                "start_ms": start,
                "end_ms": end,
                "label": f"{start//1000:02d}–{end//1000:02d}s",
                "status": status,
                "color": color,
                "pauses": len(pauses_in),
                "fillers": len(fillers_in),
                "display": f"{start//1000:02d}–{end//1000:02d}s   {color} {label}",
            })
        return windows
