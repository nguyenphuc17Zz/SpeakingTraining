from app.domains.pronunciation.contracts import PronunciationFeedbackItem


class PronunciationFeedbackPrioritizer:
    """Prioritizes and filters pronunciation issues for optimal cognitive load (Top 3 focus)."""

    SEVERITY_WEIGHTS = {
        "MUST_FIX": 1.0,
        "SHOULD_FIX": 0.65,
        "NATIVE_ALTERNATIVE": 0.40,
        "STRENGTH": 0.20,
    }

    # Pedagogical impact multipliers (meaning contrast risk)
    CATEGORY_IMPACT = {
        "pronunciation.long_vowel": 1.3,     # High meaning confusion (ojisan vs ojiisan)
        "pronunciation.small_tsu": 1.25,     # High meaning confusion (kite vs kitte)
        "pitch_accent.atamadaka": 1.15,      # High lexical contrast (ame vs ame)
        "pitch_accent.heiban": 1.10,
        "pitch_accent.nakadaka": 1.10,
        "pronunciation.phoneme.r": 1.05,
        "pronunciation.phoneme.tsu": 1.05,
        "pronunciation.mora_timing": 1.0,
        "rhythm.rushed_mora": 0.90,
        "intonation.question_rise": 1.0,
    }

    @classmethod
    def prioritize(
        cls, items: list[PronunciationFeedbackItem], max_items: int = 3
    ) -> list[PronunciationFeedbackItem]:
        """Ranks feedback items by priority score and returns top K items."""
        if not items:
            return []

        def calc_score(item: PronunciationFeedbackItem) -> float:
            sev_w = cls.SEVERITY_WEIGHTS.get(item.severity, 0.5)
            impact = cls.CATEGORY_IMPACT.get(item.issue_key, 1.0)
            return sev_w * impact

        sorted_items = sorted(items, key=calc_score, reverse=True)
        return sorted_items[:max_items]
