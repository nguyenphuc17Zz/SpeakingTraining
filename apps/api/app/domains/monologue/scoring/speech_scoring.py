"""SpeechAssessment scoring — genre-specific weights, deterministic authority."""

from __future__ import annotations

from typing import Any

from app.domains.monologue.contracts import SpeechGenre

# Default general speech weights §38
DEFAULT_WEIGHTS: dict[str, float] = {
    "fluency": 0.20,
    "coherence": 0.20,
    "grammar": 0.15,
    "vocabulary": 0.15,
    "naturalness": 0.10,
    "relevance": 0.10,
    "discourse": 0.05,
    "pronunciation": 0.05,
}

# Genre-specific overrides §39
GENRE_WEIGHTS: dict[SpeechGenre, dict[str, float]] = {
    SpeechGenre.INTERVIEW: {"relevance": 0.25, "naturalness": 0.20, "coherence": 0.20, "discourse": 0.15, "fluency": 0.10, "grammar": 0.05, "vocabulary": 0.05},
    SpeechGenre.REPORT: {"discourse": 0.25, "relevance": 0.20, "coherence": 0.20, "naturalness": 0.15, "fluency": 0.10, "grammar": 0.05, "vocabulary": 0.05},
    SpeechGenre.BUSINESS_UPDATE: {"discourse": 0.25, "relevance": 0.20, "coherence": 0.20, "naturalness": 0.15, "fluency": 0.10, "grammar": 0.05, "vocabulary": 0.05},
    SpeechGenre.STORY: {"fluency": 0.25, "coherence": 0.25, "naturalness": 0.20, "discourse": 0.15, "vocabulary": 0.10, "grammar": 0.05},
    SpeechGenre.PERSONAL: {"fluency": 0.20, "coherence": 0.20, "naturalness": 0.20, "vocabulary": 0.15, "grammar": 0.15, "discourse": 0.05, "relevance": 0.05},
    SpeechGenre.OPINION: {"relevance": 0.15, "coherence": 0.20, "fluency": 0.15, "grammar": 0.15, "vocabulary": 0.10, "naturalness": 0.10, "discourse": 0.10, "pronunciation": 0.05},
    SpeechGenre.ARGUMENT: {"relevance": 0.15, "coherence": 0.20, "discourse": 0.15, "naturalness": 0.15, "fluency": 0.15, "grammar": 0.10, "vocabulary": 0.10},
    SpeechGenre.PERSUASION: {"relevance": 0.15, "coherence": 0.20, "discourse": 0.15, "naturalness": 0.15, "fluency": 0.15, "grammar": 0.10, "vocabulary": 0.10},
    SpeechGenre.EXPLANATION: {"coherence": 0.25, "discourse": 0.20, "fluency": 0.15, "naturalness": 0.15, "relevance": 0.10, "vocabulary": 0.10, "grammar": 0.05},
    SpeechGenre.PRESENTATION: {"discourse": 0.20, "coherence": 0.20, "fluency": 0.20, "naturalness": 0.15, "relevance": 0.10, "vocabulary": 0.10, "grammar": 0.05},
}


class SpeechScoringPolicy:
    @staticmethod
    def weights_for_genre(genre: SpeechGenre | str) -> dict[str, float]:
        if isinstance(genre, str):
            try:
                genre = SpeechGenre(genre.lower())
            except Exception:
                return DEFAULT_WEIGHTS
        return GENRE_WEIGHTS.get(genre, DEFAULT_WEIGHTS)

    @classmethod
    def compute_fluency_score(
        cls,
        pause_summary: dict,
        filler_summary: dict,
        rate_quality: str,
        self_repair_summary: dict,
        duration_ms: int,
        target_ms: int,
    ) -> float:
        # Per-minute normalized penalties (not raw counts) — longer speech not unfairly penalized
        mins = max(0.5, duration_ms / 60000)
        score = 85.0
        # breakdown/stall per minute
        breakdown_pm = pause_summary.get("breakdown", 0) / mins
        stall_pm = pause_summary.get("stall", 0) / mins
        long_pm = pause_summary.get("long", 0) / mins
        score -= min(18, breakdown_pm * 14)
        score -= min(12, stall_pm * 7)
        # allow 1 long pause per minute free, penalize excess
        score -= max(0, long_pm - 1.0) * 4
        # filler — continuous curve
        fpm = filler_summary.get("filler_per_min", 0) or 0
        if fpm > 10:
            score -= 14
        elif fpm > 8:
            score -= 10
        elif fpm > 5:
            score -= 6
        elif fpm > 3:
            score -= 2
        # abandoned per minute
        abandoned_pm = self_repair_summary.get("abandoned_count", 0) / mins
        score -= min(10, abandoned_pm * 8)
        # rate
        if rate_quality == "slow":
            score -= 5
        elif rate_quality == "fast":
            score -= 3
        elif rate_quality == "too_short":
            score -= 8
        # duration endurance
        if target_ms and duration_ms:
            ratio = duration_ms / max(1, target_ms)
            if ratio < 0.5:
                score -= 12
            elif ratio < 0.75:
                score -= 6
        return max(20, min(98, round(score, 1)))

    @classmethod
    def compute_overall(
        cls,
        fluency: float,
        coherence_det: float,
        coherence_ai: float | None,
        grammar: float | None,
        vocab: float | None,
        naturalness_ai: float | None,
        relevance_ai: float | None,
        discourse: float | None,
        pronunciation: float | None,
        genre: SpeechGenre | str,
    ) -> tuple[float, dict[str, float]]:
        weights = cls.weights_for_genre(genre)
        # Coherence: single blend location (deterministic 45 / AI 55)
        coherence = coherence_det if coherence_ai is None else round(coherence_det * 0.45 + coherence_ai * 0.55, 1)
        # Build comps without mock defaults — missing signals are excluded and weights renormalized
        raw_comps: dict[str, float | None] = {
            "fluency": fluency,
            "coherence": coherence,
            "grammar": grammar,
            "vocabulary": vocab,
            "naturalness": naturalness_ai,
            "relevance": relevance_ai,
            "discourse": discourse if discourse is not None else coherence,
            "pronunciation": pronunciation,
        }
        # Filter out None (hard fail: no mock)
        comps: dict[str, float] = {k: v for k, v in raw_comps.items() if v is not None}
        # Keep only weights for available comps
        available_weights = {k: w for k, w in weights.items() if k in comps}
        if not available_weights:
            return round(coherence, 1), {}
        wsum = sum(available_weights.values())
        norm = {k: v / wsum for k, v in available_weights.items()}
        overall = sum(comps[k] * norm[k] for k in comps if k in norm)
        return round(max(0, min(100, overall)), 1), norm
