"""IdeaDensityAnalyzer §23."""

from __future__ import annotations

import re
from collections import Counter


class IdeaDensityAnalyzer:
    @staticmethod
    def analyze(transcript: str) -> dict:
        # Split into clauses/sentences
        sentences = [s.strip() for s in re.split(r"[。！？\n]+", transcript) if s.strip()]
        # Supporting details: sentences with 例えば/具体的/たとえば/など or numbers
        detail_cues = ["例えば", "たとえば", "具体的", "たとえ", "例として", "数字", "データ", "具体例"]
        example_count = sum(1 for s in sentences if any(c in s for c in detail_cues) or re.search(r"\d+", s))
        supporting = sum(1 for s in sentences if len(s) > 15) - example_count
        supporting = max(0, supporting)

        # Unique vs repeated ideas: Jaccard on sentence n-grams (simple)
        def norm(s: str) -> str:
            return re.sub(r"[はがのをにでと、\s]+", "", s.lower())

        normalized = [norm(s) for s in sentences]
        # Repeated: same normalized form appears >1
        counts = Counter(normalized)
        repeated = sum(1 for v in counts.values() if v > 1)
        unique = len([k for k, v in counts.items() if v >= 1])

        # Relevant claims: sentences with opinion/cause markers (heuristic)
        claim_markers = ["と思う", "考える", "必要", "大切", "重要", "べき", "ため", "ので", "から"]
        relevant_claims = sum(1 for s in sentences if any(m in s for m in claim_markers))

        # Density: unique ideas per 100 chars (avoid verbosity reward)
        chars = max(1, len(re.sub(r"\s", "", transcript)))
        density = round(unique / (chars / 100), 2) if chars else 0

        # If many sentences but few unique → lower density
        if len(sentences) > 6 and unique <= 2:
            density = round(density * 0.5, 2)

        return {
            "unique_ideas": unique,
            "supporting_details": supporting,
            "examples": example_count,
            "repeated_ideas": repeated,
            "relevant_claims": relevant_claims,
            "idea_density_score": density,
            "sentence_count": len(sentences),
        }
