from app.domains.conversation_intelligence.contracts import (
    AnalysisConfidence,
    CorrectionItem,
    CorrectionSeverity,
)


class FeedbackPrioritizer:
    """Ranks and budgets linguistic feedback items using Maximal Marginal Relevance (MMR)
    to prevent cognitive overload (Cognitive Load Theory - Sweller, 1988).
    """

    SEVERITY_WEIGHTS = {
        CorrectionSeverity.MUST_FIX: 100,
        CorrectionSeverity.SHOULD_FIX: 70,
        CorrectionSeverity.NATIVE_ALTERNATIVE: 40,
        CorrectionSeverity.IGNORE: 10,
    }

    CONFIDENCE_WEIGHTS = {
        AnalysisConfidence.HIGH: 1.0,
        AnalysisConfidence.MEDIUM: 0.75,
        AnalysisConfidence.LOW: 0.4,
    }

    @classmethod
    def calculate_priority_score(cls, item: CorrectionItem) -> float:
        base_sev = cls.SEVERITY_WEIGHTS.get(item.severity, 30)
        conf_multiplier = cls.CONFIDENCE_WEIGHTS.get(item.confidence, 0.75)
        # Use internal severity score if present as subtle tiebreaker
        return (base_sev * 0.8 + item.severity_score * 0.2) * conf_multiplier

    @classmethod
    def calculate_redundancy_similarity(cls, a: CorrectionItem, b: CorrectionItem) -> float:
        """Calculates pedagogical redundancy between two correction items.

        Returns value in [0.0, 1.0] where 1.0 means highly redundant/repetitive.
        """
        sim = 0.0

        # 1. Category redundancy (e.g. both are PARTICLE or both are GRAMMAR)
        if a.category == b.category:
            sim += 0.45

        # 2. Token overlap in original snippet or correction
        orig_a = set(a.original.strip().lower())
        orig_b = set(b.original.strip().lower())
        if orig_a and orig_b:
            jaccard_orig = len(orig_a & orig_b) / len(orig_a | orig_b)
            sim += 0.35 * jaccard_orig

        # 3. Exact target token match
        if a.original.strip() == b.original.strip():
            sim += 0.20

        return min(1.0, sim)

    @classmethod
    def prioritize(
        cls,
        corrections: list[CorrectionItem],
        max_budget: int = 3,
        mode: str = "coaching",
        lambda_param: float | None = None,
    ) -> list[CorrectionItem]:
        """Ranks corrections using Maximal Marginal Relevance (MMR) (Carbonell & Goldstein, 1998).

        Balances pedagogical severity against error diversity to prevent cognitive overload.
        """
        eligible = [c for c in corrections if c.severity != CorrectionSeverity.IGNORE]
        if len(eligible) <= max_budget:
            return sorted(eligible, key=cls.calculate_priority_score, reverse=True)

        # Set trade-off lambda parameter
        if lambda_param is not None:
            lam = lambda_param
        elif mode == "strict":
            lam = 0.85
        else:
            lam = 0.65  # Coaching balance: 65% severity, 35% novelty/diversity

        raw_scores = [cls.calculate_priority_score(c) for c in eligible]
        max_score = max(raw_scores) if raw_scores else 1.0
        norm_scores = [s / max(1e-6, max_score) for s in raw_scores]

        selected_indices: list[int] = []
        candidate_indices = list(range(len(eligible)))

        # 1. Pick first item: highest normalized priority
        first_idx = max(candidate_indices, key=lambda idx: norm_scores[idx])
        selected_indices.append(first_idx)
        candidate_indices.remove(first_idx)

        # 2. Greedily pick remaining items using MMR
        while len(selected_indices) < max_budget and candidate_indices:
            best_idx = None
            best_mmr = -float("inf")

            for c_idx in candidate_indices:
                c_item = eligible[c_idx]
                max_sim = max(
                    cls.calculate_redundancy_similarity(c_item, eligible[s_idx])
                    for s_idx in selected_indices
                )
                mmr_val = lam * norm_scores[c_idx] - (1.0 - lam) * max_sim
                if mmr_val > best_mmr:
                    best_mmr = mmr_val
                    best_idx = c_idx

            if best_idx is not None:
                selected_indices.append(best_idx)
                candidate_indices.remove(best_idx)
            else:
                break

        return [eligible[idx] for idx in selected_indices]

