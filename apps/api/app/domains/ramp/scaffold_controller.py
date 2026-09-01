"""ScaffoldController — builds concrete scaffold content and manages fading.

§4 Scaffold → Fade, §5 Support Levels, §30 Dynamic Support Decay.
"""

from __future__ import annotations

from app.domains.ramp.contracts import (
    RampScaffold,
    RampSupportLevel,
    RampTaskSpec,
    SUPPORT_INDEPENDENCE_MULTIPLIER,
)


class ScaffoldController:
    """
    Maps abstract support level to concrete learner-facing scaffold content.

    Support level hierarchy:
      0 = NONE            → no hints
      1 = TOPIC_ONLY      → only the topic
      2 = KEYWORDS        → topic + 3–5 keywords
      3 = GUIDED_QUESTION → structured questions in Japanese
      4 = SENTENCE_STARTER → 〜ました。/〜と思います。
      5 = STRUCTURE_OUTLINE → PREP/REASON/EXAMPLE/SUMMARY
      6 = EXAMPLE         → a full example response (reveals answer — heavy penalty)
      7 = TRANSLATION_REF → native-language scaffolding (reveals answer — heaviest penalty)
    """

    def build_scaffold(
        self,
        support_level: int,
        task_spec: RampTaskSpec,
    ) -> RampScaffold:
        """Build scaffold object for the given support level."""
        sc = RampScaffold(support_level=support_level)

        if support_level >= RampSupportLevel.TOPIC_ONLY.value:
            sc.topic = task_spec.topic

        if support_level >= RampSupportLevel.KEYWORDS.value:
            sc.keywords = task_spec.scaffold.keywords or task_spec.keywords_for_production

        if support_level >= RampSupportLevel.GUIDED_QUESTION.value:
            sc.guided_questions = task_spec.scaffold.guided_questions or []

        if support_level >= RampSupportLevel.SENTENCE_STARTER.value:
            sc.sentence_starter = task_spec.scaffold.sentence_starter

        if support_level >= RampSupportLevel.STRUCTURE_OUTLINE.value:
            sc.structure_outline = task_spec.scaffold.structure_outline or [
                "導入（イントロ）",
                "理由",
                "例",
                "まとめ",
            ]

        if support_level >= RampSupportLevel.EXAMPLE.value:
            sc.example_response = task_spec.scaffold.example_response

        if support_level >= RampSupportLevel.TRANSLATION_REFERENCE.value:
            sc.translation_reference = task_spec.scaffold.translation_reference

        return sc

    def get_independence_multiplier(self, support_level: int) -> float:
        """Returns mastery multiplier for the support level used. §5"""
        return SUPPORT_INDEPENDENCE_MULTIPLIER.get(support_level, 0.5)

    def is_answer_revealing(self, support_level: int) -> bool:
        """Levels 6–7 directly reveal the answer. §5"""
        return support_level >= RampSupportLevel.EXAMPLE.value

    def fade_support(self, current: int) -> int:
        """Remove one support layer. Floor = 0."""
        return max(0, current - 1)

    def restore_support(self, current: int) -> int:
        """Restore one support layer. Ceiling = 7."""
        return min(7, current + 1)

    def get_level_label(self, support_level: int) -> str:
        labels = {
            0: "No support",
            1: "Topic only",
            2: "Keywords",
            3: "Guided questions",
            4: "Sentence starter",
            5: "Structure outline",
            6: "Example response",
            7: "Translation reference",
        }
        return labels.get(support_level, "Unknown")

    def describe_support(self, support_level: int) -> str:
        """Human-readable description for UI. §5"""
        descs = {
            0: "Fully independent — no hints",
            1: "Topic shown only",
            2: "Topic + keywords provided",
            3: "Guided questions to structure your answer",
            4: "Sentence starter provided",
            5: "Full outline structure provided",
            6: "Example response shown",
            7: "Translation reference available",
        }
        return descs.get(support_level, "")
