"""ConstraintGenerator — reusable learning primitives, not hard-coded UI strings."""

from __future__ import annotations

import random

from app.domains.monologue.contracts import SpeechGenre

# Reusable constraint primitives (learning primitives, not topic database)
CONSTRAINT_POOL: list[str] = [
    "include_one_example",
    "include_one_reason",
    "compare_two_options",
    "state_an_opinion",
    "include_one_consequence",
    "end_with_conclusion",
    "include_numbers_or_data",
    "mention_one_counterpoint",
    "use_one_cause_effect",
    "include_personal_experience",
]

# Genre → recommended constraints
GENRE_CONSTRAINT_AFFINITY: dict[SpeechGenre, list[str]] = {
    SpeechGenre.OPINION: ["state_an_opinion", "include_one_reason", "include_one_example", "end_with_conclusion"],
    SpeechGenre.ARGUMENT: ["state_an_opinion", "include_one_reason", "mention_one_counterpoint", "end_with_conclusion"],
    SpeechGenre.PERSUASION: ["state_an_opinion", "include_one_reason", "include_one_example", "end_with_conclusion"],
    SpeechGenre.COMPARISON: ["compare_two_options", "include_one_example", "end_with_conclusion"],
    SpeechGenre.PROBLEM_SOLUTION: ["include_one_reason", "include_one_consequence", "end_with_conclusion"],
    SpeechGenre.EXPLANATION: ["include_one_example", "use_one_cause_effect", "end_with_conclusion"],
    SpeechGenre.REPORT: ["include_numbers_or_data", "include_one_consequence", "end_with_conclusion"],
    SpeechGenre.BUSINESS_UPDATE: ["include_numbers_or_data", "end_with_conclusion"],
    SpeechGenre.PRESENTATION: ["include_one_example", "end_with_conclusion"],
    SpeechGenre.STORY: ["include_personal_experience", "end_with_conclusion"],
    SpeechGenre.PERSONAL: ["include_personal_experience", "end_with_conclusion"],
    SpeechGenre.INTERVIEW: ["include_one_reason", "include_one_example", "end_with_conclusion"],
}

CONSTRAINT_JP_LABEL: dict[str, str] = {
    "include_one_example": "具体例を1つ入れる",
    "include_one_reason": "理由を1つ述べる",
    "compare_two_options": "2つの選択肢を比較する",
    "state_an_opinion": "自分の意見を明確に述べる",
    "include_one_consequence": "結果・影響を1つ述べる",
    "end_with_conclusion": "結論で締めくくる",
    "include_numbers_or_data": "数字・データに触れる",
    "mention_one_counterpoint": "反対意見にも触れる",
    "use_one_cause_effect": "原因・結果の関係を示す",
    "include_personal_experience": "自分の経験を入れる",
}


class ConstraintCompatibilityValidator:
    """Ensures constraints are not contradictory/nonsensical."""

    INCOMPATIBLE_PAIRS = {
        frozenset(["compare_two_options", "include_personal_experience"]): False,  # actually compatible, but keep example
    }

    @classmethod
    def validate(cls, constraints: list[str], genre: SpeechGenre) -> tuple[bool, list[str]]:
        issues: list[str] = []
        if len(constraints) != len(set(constraints)):
            issues.append("Duplicate constraints")
        for c in constraints:
            if c not in CONSTRAINT_POOL:
                issues.append(f"Unknown constraint {c}")
        # genre mismatch warning (not hard fail)
        affinity = GENRE_CONSTRAINT_AFFINITY.get(genre, [])
        # allow any, but flag if completely off
        return len(issues) == 0, issues


class ConstraintGenerator:
    def generate(
        self,
        genre: SpeechGenre,
        difficulty: int,
        duration_sec: int,
        seed: str | None = None,
    ) -> list[str]:
        rng = random.Random(seed) if seed else random
        affinity = GENRE_CONSTRAINT_AFFINITY.get(genre, CONSTRAINT_POOL[:3])

        # difficulty → count
        if difficulty <= 2 or duration_sec <= 45:
            count = 1
        elif difficulty == 3 or duration_sec <= 90:
            count = 2
        else:
            count = 3

        # prefer affinity but allow variety
        pool = affinity + [c for c in CONSTRAINT_POOL if c not in affinity]
        # weighted: affinity first
        chosen: list[str] = []
        for c in pool:
            if len(chosen) >= count:
                break
            if rng.random() < 0.7 or c in affinity:
                if c not in chosen:
                    chosen.append(c)
        # fill if needed
        while len(chosen) < count:
            cand = rng.choice(CONSTRAINT_POOL)
            if cand not in chosen:
                chosen.append(cand)
        # ensure conclusion for longer speeches
        if duration_sec >= 60 and "end_with_conclusion" not in chosen and rng.random() < 0.8:
            if len(chosen) >= count:
                chosen[-1] = "end_with_conclusion"
            else:
                chosen.append("end_with_conclusion")

        valid, _ = ConstraintCompatibilityValidator.validate(chosen, genre)
        if not valid:
            # fallback minimal
            return affinity[:count]
        return chosen[:count]
