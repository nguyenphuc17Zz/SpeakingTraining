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

        # Psycholinguistic Cognitive Strain & Weibull Hazard Analysis
        strain_data = cls.compute_cognitive_strain(pauses, speech_duration_ms)

        summary = {
            "micro": sum(1 for p in pauses if p.pause_class == PauseClass.MICRO_PAUSE),
            "normal": sum(1 for p in pauses if p.pause_class == PauseClass.NORMAL_PAUSE),
            "long": sum(1 for p in pauses if p.pause_class == PauseClass.LONG_PAUSE),
            "stall": sum(1 for p in pauses if p.pause_class == PauseClass.STALL),
            "breakdown": sum(1 for p in pauses if p.pause_class == PauseClass.BREAKDOWN),
            "total": len(pauses),
            "cognitive_pause_strain_index": strain_data["cpsi"],
            "grammatical_pause_ratio": strain_data["grammatical_pause_ratio"],
            "hesitation_pause_count": strain_data["hesitation_pause_count"],
            "hazard_risk_level": strain_data["hazard_risk_level"],
        }
        return pauses, summary

    # SLA Psycholinguistic context strain weights (Goldman-Eisler 1968, De Jong 2016)
    CONTEXT_STRAIN_WEIGHTS: dict[PauseContext, float] = {
        PauseContext.SENTENCE_BOUNDARY: 0.25,
        PauseContext.CLAUSE_BOUNDARY: 0.35,
        PauseContext.BEFORE_NEW_IDEA: 0.50,
        PauseContext.BEFORE_PREDICATE: 0.85,
        PauseContext.AFTER_FILLER: 1.10,
        PauseContext.INSIDE_PHRASE: 1.35,
        PauseContext.AFTER_SELF_REPAIR: 1.50,
        PauseContext.UNKNOWN: 0.70,
    }

    WEIBULL_LAMBDA_MS: float = 750.0  # Scale parameter
    WEIBULL_K_SHAPE: float = 1.25     # Shape parameter

    @classmethod
    def weibull_survival(cls, duration_ms: float) -> float:
        """
        Parametric Weibull Survival Function: S(t) = exp(-(t / lambda)^k).
        Returns probability of a natural fluent pause surviving beyond duration_ms.
        """
        if duration_ms <= 0:
            return 1.0
        import math
        ratio = duration_ms / cls.WEIBULL_LAMBDA_MS
        return math.exp(-math.pow(ratio, cls.WEIBULL_K_SHAPE))

    @classmethod
    def compute_cognitive_strain(cls, pauses: list[PauseEvent], speech_duration_ms: int) -> dict[str, Any]:
        """
        Computes Cognitive Pause Strain Index (CPSI) by weighting pause duration survival hazard
        with syntactic constituent context. Distinguishes natural physiological pauses from lexical search breakdowns.
        """
        if not pauses or speech_duration_ms <= 0:
            return {
                "cpsi": 0.0,
                "grammatical_pause_ratio": 1.0,
                "hesitation_pause_count": 0,
                "hazard_risk_level": "low",
            }

        speech_sec = max(1.0, speech_duration_ms / 1000.0)
        total_strain = 0.0
        grammatical_count = 0
        hesitation_count = 0

        for p in pauses:
            w_ctx = cls.CONTEXT_STRAIN_WEIGHTS.get(p.context, 0.70)
            surv = cls.weibull_survival(p.duration_ms)
            hazard_strain_prob = 1.0 - surv
            dur_sec = p.duration_ms / 1000.0

            # Strain contribution
            total_strain += w_ctx * hazard_strain_prob * dur_sec

            if p.context in (PauseContext.SENTENCE_BOUNDARY, PauseContext.CLAUSE_BOUNDARY):
                grammatical_count += 1

            if w_ctx >= 0.85 and p.duration_ms >= 800:
                hesitation_count += 1

        cpsi = round((100.0 / speech_sec) * total_strain, 2)
        gramm_ratio = round(grammatical_count / max(1, len(pauses)), 3)

        if cpsi < 12.0:
            risk = "low"
        elif cpsi < 30.0:
            risk = "moderate"
        else:
            risk = "high"

        return {
            "cpsi": cpsi,
            "grammatical_pause_ratio": gramm_ratio,
            "hesitation_pause_count": hesitation_count,
            "hazard_risk_level": risk,
        }
