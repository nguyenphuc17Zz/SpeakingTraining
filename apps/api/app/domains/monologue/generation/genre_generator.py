"""SpeechGenreGenerator — dynamic selection based on learner state."""

from __future__ import annotations

import random
from typing import Any

from app.domains.monologue.contracts import SpeechGenre, SpeechTopicDomain
from app.domains.monologue.generation.genre_ontology import (
    ALL_GENRES,
    GENRE_DURATION_AFFINITY,
)


class SpeechGenreGenerator:
    """Selects genre from controlled ontology based on learner weakness/goals/duration/history."""

    # Weakness → genre mapping (conceptual policy)
    WEAKNESS_MAP: dict[str, list[SpeechGenre]] = {
        "coherence": [SpeechGenre.PROBLEM_SOLUTION, SpeechGenre.EXPLANATION, SpeechGenre.REPORT],
        "argumentation": [SpeechGenre.OPINION, SpeechGenre.ARGUMENT, SpeechGenre.PERSUASION],
        "storytelling": [SpeechGenre.STORY, SpeechGenre.REFLECTION],
        "business": [SpeechGenre.REPORT, SpeechGenre.BUSINESS_UPDATE, SpeechGenre.PRESENTATION, SpeechGenre.INTERVIEW],
        "fluency": [SpeechGenre.PERSONAL, SpeechGenre.STORY],
        "vocabulary": [SpeechGenre.EXPLANATION, SpeechGenre.COMPARISON],
        "discourse": [SpeechGenre.PRESENTATION, SpeechGenre.ARGUMENT],
    }

    CAREER_MAP: dict[str, list[SpeechGenre]] = {
        "business": [SpeechGenre.REPORT, SpeechGenre.BUSINESS_UPDATE, SpeechGenre.PRESENTATION],
        "interview": [SpeechGenre.INTERVIEW, SpeechGenre.PRESENTATION],
        "travel": [SpeechGenre.PERSONAL, SpeechGenre.STORY],
        "education": [SpeechGenre.EXPLANATION, SpeechGenre.PRESENTATION],
    }

    def select(
        self,
        learner_level: str,
        recent_genres: list[str],
        weaknesses: list[dict[str, Any]],
        career_goals: list[str] | None,
        duration_sec: int,
        seed: str | None = None,
    ) -> SpeechGenre:
        rng = random.Random(seed) if seed else random

        candidates: list[tuple[SpeechGenre, float]] = []

        # Score by weakness — exact key match, no substring join
        weak_keys = [str(w.get("key") or w.get("type") or "").lower() for w in (weaknesses or [])]
        for genre in ALL_GENRES:
            score = 0.5
            for wk in weak_keys:
                # exact weakness key match
                if wk in self.WEAKNESS_MAP and genre in self.WEAKNESS_MAP[wk]:
                    score += 0.25
                # direct containment fallback
                if wk and wk in genre.value:
                    score += 0.15
            # career bias
            if career_goals:
                for cg in career_goals:
                    cgl = cg.lower()
                    for cm, gs in self.CAREER_MAP.items():
                        if cm in cgl and genre in gs:
                            score += 0.2
            # duration affinity
            aff = GENRE_DURATION_AFFINITY.get(genre, [])
            if duration_sec in aff:
                score += 0.15
            elif abs(duration_sec - (aff[0] if aff else 60)) < 30:
                score += 0.05
            # anti-repetition penalty
            if genre.value in (recent_genres or [])[-3:]:
                score -= 0.35
                if recent_genres and recent_genres[-1] == genre.value:
                    score -= 0.25
            # beginners → simpler genres
            if learner_level.upper() in ("N5", "N4") and genre in (
                SpeechGenre.ARGUMENT, SpeechGenre.CRITIQUE, SpeechGenre.PRESENTATION, SpeechGenre.BUSINESS_UPDATE
            ):
                score -= 0.2
            candidates.append((genre, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        # top-3 weighted random
        top = candidates[:5]
        weights = [max(0.1, s) for _, s in top]
        chosen = rng.choices([g for g, _ in top], weights=weights, k=1)[0]
        return chosen

    def list_all(self) -> list[str]:
        return [g.value for g in ALL_GENRES]
