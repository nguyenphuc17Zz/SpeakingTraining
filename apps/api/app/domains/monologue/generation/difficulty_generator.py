"""DifficultyGenerator & support-level policy."""

from __future__ import annotations

from app.domains.monologue.contracts import SpeechGenre, SpeechSupportLevel


class DifficultyGenerator:
    """Maps learner level + genre + duration → difficulty 1-5 and scaffold."""

    LEVEL_MAP: dict[str, int] = {"N5": 1, "N4": 2, "N3": 3, "N2": 4, "N1": 5}

    def difficulty_for(
        self,
        level: str,
        genre: SpeechGenre,
        duration_sec: int,
        weakness_factor: float | None = None,
    ) -> int:
        base = self.LEVEL_MAP.get(level.upper(), 3)
        # longer duration → +1 (cap once)
        if duration_sec >= 180:
            base = min(5, base + 1)
        elif duration_sec >= 120:
            base = min(5, base + 1)
        # demanding genres +1
        if genre.value in ("argument", "critique", "presentation", "business_update"):
            base = min(5, base + 1)
        if weakness_factor is not None and weakness_factor > 0.7:
            base = max(1, base - 1)  # weak area → slightly lower difficulty for success
        return max(1, min(5, base))

    def support_level_for(
        self,
        difficulty: int,
        level: str,
        genre: SpeechGenre,
        automaticity: float | None = None,
    ) -> SpeechSupportLevel:
        # gradual reduction as level/automaticity improves
        if automaticity is not None and automaticity > 0.75:
            return SpeechSupportLevel.MINIMAL
        if level.upper() in ("N5", "N4"):
            if difficulty <= 2:
                return SpeechSupportLevel.STRUCTURE
            if difficulty == 3:
                return SpeechSupportLevel.GUIDED_QUESTIONS
            return SpeechSupportLevel.KEYWORDS
        if level.upper() == "N3":
            if difficulty <= 2:
                return SpeechSupportLevel.STRUCTURE
            if difficulty == 3:
                return SpeechSupportLevel.GUIDED_QUESTIONS
            return SpeechSupportLevel.KEYWORDS
        # N2/N1
        if difficulty >= 4:
            return SpeechSupportLevel.MINIMAL
        return SpeechSupportLevel.STRUCTURE

    def prep_sec_for(
        self,
        difficulty: int,
        duration_sec: int,
        level: str,
    ) -> int:
        if duration_sec <= 45:
            return 15 if level.upper() not in ("N5",) else 30
        if duration_sec <= 60:
            return 30
        if duration_sec <= 120:
            return 30 if difficulty >= 3 else 60
        return 60


class PreparationHintGenerator:
    """Hints must help organization, not write speech for user (§46)."""

    @staticmethod
    def keywords_hint(topic: str, genre: SpeechGenre, level: str) -> list[str]:
        # Placeholder: AI will generate real keywords; fallback returns generic axes
        return []

    @staticmethod
    def guided_questions(genre: SpeechGenre) -> list[str]:
        mapping = {
            SpeechGenre.OPINION: ["あなたの意見は何ですか？", "なぜそう思いますか？", "具体例を1つ挙げてください。"],
            SpeechGenre.PROBLEM_SOLUTION: ["どんな問題ですか？", "原因は何ですか？", "解決策を提案してください。"],
            SpeechGenre.REPORT: ["現状はどうですか？", "問題と影響は？", "次のアクションは？"],
            SpeechGenre.INTERVIEW: ["あなたの強みは？", "具体的な経験は？", "どう貢献できますか？"],
        }
        return mapping.get(genre, ["あなたの意見は何ですか？", "理由は？", "例を挙げてください。"])

    @staticmethod
    def structure_outline(genre: SpeechGenre) -> list[str]:
        from app.domains.monologue.generation.genre_ontology import GENRE_STRUCTURE

        return GENRE_STRUCTURE.get(genre, ["Introduction", "Point", "Reason", "Example", "Conclusion"])
