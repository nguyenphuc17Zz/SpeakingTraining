"""PauseAnalyzer §18/19."""

from __future__ import annotations

import re

from app.domains.monologue.contracts import PauseClass, PauseContext, PauseEvent


class PauseAnalyzer:
    # thresholds ms (configurable, tuned with real data)
    MICRO = 500
    NORMAL = 1000
    LONG = 1500
    STALL = 3000

    @classmethod
    def classify(cls, duration_ms: int) -> PauseClass:
        if duration_ms < cls.MICRO:
            return PauseClass.MICRO_PAUSE
        if duration_ms < cls.NORMAL:
            return PauseClass.NORMAL_PAUSE
        if duration_ms < cls.LONG:
            return PauseClass.LONG_PAUSE
        if duration_ms < cls.STALL:
            return PauseClass.STALL
        return PauseClass.BREAKDOWN

    @staticmethod
    def infer_context(
        pause_start_ms: int,
        pause_end_ms: int,
        transcript: str,
        words: list[dict],
        filler_events: list[dict] | None = None,
        repair_events: list[dict] | None = None,
    ) -> PauseContext:
        # Find surrounding words
        prev_word = None
        next_word = None
        for w in words or []:
            if w.get("end_ms", 0) <= pause_start_ms:
                prev_word = w
            if w.get("start_ms", 0) >= pause_end_ms and next_word is None:
                next_word = w
        # Check if after filler
        if filler_events:
            for f in filler_events:
                if f.get("end_ms") and abs(f["end_ms"] - pause_start_ms) < 300:
                    return PauseContext.AFTER_FILLER
        if repair_events:
            for r in repair_events:
                if r.get("start_ms") and abs(r["start_ms"] - pause_start_ms) < 500:
                    return PauseContext.AFTER_SELF_REPAIR
        # Check sentence boundary: prev word ends with 。！？ or end of transcript segment
        if prev_word and re.search(r"[。！？.!?]$", str(prev_word.get("word", "")).strip()):
            return PauseContext.SENTENCE_BOUNDARY
        # Clause boundary: wider conjunctive set
        if prev_word and re.search(r"[、,]$|て$|が$|けど$|ので$|から$|し$|たり$|ながら$|ても$|のに$", str(prev_word.get("word", "")).strip()):
            return PauseContext.CLAUSE_BOUNDARY
        # Before predicate: use POS if available, fallback to suffix heuristic
        if next_word:
            # try POS from word dict if provider supplied
            pos = str(next_word.get("pos") or "")
            if pos in ("動詞", "形容詞", "形容動詞"):
                return PauseContext.BEFORE_PREDICATE
            if re.search(r"(する|です|ます|だ|である|なる|した|された|できる|ある|ない)$", str(next_word.get("word", "")).strip()):
                return PauseContext.BEFORE_PREDICATE
        if prev_word is None or next_word is None:
            return PauseContext.BEFORE_NEW_IDEA
        # inside phrase if no boundary marker — infer from absence of clause markers
        if prev_word and next_word:
            # if both words are within same clause (no punctuation), consider inside phrase
            return PauseContext.INSIDE_PHRASE
        return PauseContext.UNKNOWN

    @classmethod
    def analyze(
        cls,
        words: list[dict],
        speech_duration_ms: int,
        transcript: str = "",
        filler_events: list[dict] | None = None,
        repair_events: list[dict] | None = None,
    ) -> tuple[list[PauseEvent], dict]:
        pauses: list[PauseEvent] = []
        if not words or len(words) < 2:
            return pauses, {"micro": 0, "normal": 0, "long": 0, "stall": 0, "breakdown": 0, "total": 0}

        # Sort by start_ms
        words_sorted = sorted([w for w in words if w.get("start_ms") is not None and w.get("end_ms") is not None], key=lambda x: x["start_ms"])
        for i in range(1, len(words_sorted)):
            prev = words_sorted[i - 1]
            cur = words_sorted[i]
            gap = int(cur["start_ms"] - prev["end_ms"])
            if gap < 150:  # ignore tiny gaps (ASR jitter)
                continue
            pclass = cls.classify(gap)
            ctx = cls.infer_context(prev["end_ms"], cur["start_ms"], transcript, words_sorted, filler_events, repair_events)

            pauses.append(PauseEvent(
                start_ms=int(prev["end_ms"]),
                end_ms=int(cur["start_ms"]),
                duration_ms=gap,
                pause_class=pclass,
                context=ctx,
            ))

        summary = {
            "micro": sum(1 for p in pauses if p.pause_class == PauseClass.MICRO_PAUSE),
            "normal": sum(1 for p in pauses if p.pause_class == PauseClass.NORMAL_PAUSE),
            "long": sum(1 for p in pauses if p.pause_class == PauseClass.LONG_PAUSE),
            "stall": sum(1 for p in pauses if p.pause_class == PauseClass.STALL),
            "breakdown": sum(1 for p in pauses if p.pause_class == PauseClass.BREAKDOWN),
            "total": len(pauses),
        }
        return pauses, summary
