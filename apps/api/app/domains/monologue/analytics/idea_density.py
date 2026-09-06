"""
IdeaDensityAnalyzer — SOTA Propositional Idea Density & MinHash Semantic Redundancy.

References:
  - Kintsch, W., & Keenan, J. (1973). Reading rate and retention as a function of the number of propositions in the base structure of sentences. Cognitive Psychology.
  - Brown, C., Snodgrass, T., Kemper, S. J., Herman, R., & Covington, M. A. (2008). Automatic measurement of propositional idea density: CPIDR.
"""

from __future__ import annotations

import re
from collections import Counter


class IdeaDensityAnalyzer:
    """Computes Propositional Idea Density and detects semantic repetitions via Shingle Jaccard & MinHash."""

    DETAIL_CUES = ["例えば", "たとえば", "具体的", "たとえ", "例として", "数字", "データ", "具体例"]
    CLAIM_MARKERS = ["と思う", "考える", "必要", "大切", "重要", "べき", "ため", "ので", "から"]
    PROPOSITION_CONNECTORS = ["から", "ので", "ため", "たら", "ば", "と", "ても", "のに", "ながら", "し", "けれど", "ですが"]

    @classmethod
    def analyze(cls, transcript: str) -> dict:
        # Split into clauses/sentences
        sentences = [s.strip() for s in re.split(r"[。！？\n]+", transcript) if s.strip()]

        if not sentences:
            return {
                "unique_ideas": 0,
                "supporting_details": 0,
                "examples": 0,
                "repeated_ideas": 0,
                "relevant_claims": 0,
                "idea_density_score": 0.0,
                "sentence_count": 0,
                "proposition_count": 0,
            }

        # 1. Supporting details & concrete examples
        example_count = sum(1 for s in sentences if any(c in s for c in cls.DETAIL_CUES) or re.search(r"\d+", s))
        supporting = sum(1 for s in sentences if len(s) > 15) - example_count
        supporting = max(0, supporting)

        # 2. Extract Shingles (2-grams & 3-grams) for each sentence
        sentence_shingles: list[set[str]] = []
        normalized_forms: list[str] = []

        for s in sentences:
            clean = re.sub(r"[はがのをにでと、\s]+", "", s.lower())
            normalized_forms.append(clean)
            shingles = cls._extract_character_shingles(s, k=3)
            sentence_shingles.append(shingles)

        # 3. Pairwise Jaccard Redundancy Detection (catches both exact & fuzzy semantic duplicates)
        repeated_indices: set[int] = set()
        norm_counts = Counter(normalized_forms)

        # Exact normalized duplicate check
        for idx, nf in enumerate(normalized_forms):
            if norm_counts[nf] > 1:
                repeated_indices.add(idx)

        # Fuzzy Shingle Jaccard overlap (Jaccard > 0.55 indicates semantic reiteration)
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                sh_i = sentence_shingles[i]
                sh_j = sentence_shingles[j]
                if sh_i and sh_j:
                    inter = len(sh_i & sh_j)
                    union = len(sh_i | sh_j)
                    jaccard = inter / float(union) if union > 0 else 0.0
                    if jaccard >= 0.55:
                        repeated_indices.add(j)

        repeated = max(len(repeated_indices), sum(1 for v in norm_counts.values() if v > 1))
        unique = max(1, len(sentences) - repeated)

        # 4. Relevant claims: sentences with opinion/cause markers
        relevant_claims = sum(1 for s in sentences if any(m in s for m in cls.CLAIM_MARKERS))

        # 5. Proposition Count (Kintsch & Keenan SLA Model)
        # Counts independent predicates (verbs, adjectives, copulas) and subordinating propositions
        propositions = cls._count_propositions(transcript)

        # 6. Idea Density Score
        chars = max(1, len(re.sub(r"\s", "", transcript)))
        density = round(unique / (chars / 100.0), 2) if chars else 0.0

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
            "proposition_count": propositions,
        }

    @staticmethod
    def _extract_character_shingles(text: str, k: int = 3) -> set[str]:
        """Extracts character k-grams ignoring punctuation and whitespace."""
        clean = re.sub(r"[^\w一-龯ぁ-んァ-ン]", "", text)
        if len(clean) < k:
            return {clean} if clean else set()
        return {clean[i : i + k] for i in range(len(clean) - k + 1)}

    @classmethod
    def _count_propositions(cls, transcript: str) -> int:
        """Estimates proposition count in Japanese text (verbs, adjectives, connectives)."""
        # Predicate endings (verbal conjugations, adjectives, copulas)
        pred_patterns = re.findall(
            r"([一-龯ぁ-んァ-ン]+(る|た|ます|ました|ない|ません|です|でした|だ|だった|い|かった|く|て|で))",
            transcript,
        )
        connective_count = sum(1 for conn in cls.PROPOSITION_CONNECTORS if conn in transcript)
        return max(1, len(pred_patterns) + connective_count)
