"""ScaffoldController — builds concrete scaffold content and manages fading.

§4 Scaffold → Fade, §5 Support Levels, §30 Dynamic Support Decay.
"""

from __future__ import annotations

from app.domains.ramp.contracts import (
    SUPPORT_INDEPENDENCE_MULTIPLIER,
    RampScaffold,
    RampSupportLevel,
    RampTaskSpec,
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

    @classmethod
    def calculate_pid_support(
        cls,
        current_level: int,
        performance_history: list[float],
        target_score: float = 75.0,
        kp: float = 0.04,
        ki: float = 0.015,
        kd: float = 0.02,
    ) -> PIDScaffoldDecision:
        """
        SOTA Closed-Loop PID (Proportional-Integral-Derivative) Scaffold Fading Engine.
        Dynamically modulates support levels according to Vygotskian Zone of Proximal Development (ZPD).
        Prevents cognitive whiplash (overshoot/chattering) via derivative dampening and integral anti-windup.
        """
        if not performance_history:
            return PIDScaffoldDecision(
                recommended_level=current_level,
                control_signal=0.0,
                p_term=0.0,
                i_term=0.0,
                d_term=0.0,
                reason="No history available; maintaining current scaffold level.",
            )

        # Recent history window (up to last 5 attempts)
        recent = performance_history[-5:]
        errors = [target_score - score for score in recent]
        current_error = errors[-1]

        # 1. Proportional Term: immediate reaction to latest attempt
        p_term = kp * current_error

        # 2. Integral Term: accumulated error with anti-windup clamp [-2.5, +2.5]
        raw_integral = sum(errors)
        i_term = max(-2.5, min(2.5, ki * raw_integral))

        # 3. Derivative Term: velocity of change (dampens sudden jumps)
        prev_error = errors[-2] if len(errors) >= 2 else current_error
        d_term = kd * (current_error - prev_error)

        control_signal = p_term + i_term + d_term

        # Continuous control mapped to discrete level shift with hysteresis deadband [-0.35, +0.35]
        level_shift = 0
        if control_signal > 0.35:
            level_shift = max(1, int(round(control_signal)))
        elif control_signal < -0.35:
            level_shift = min(-1, int(round(control_signal)))

        recommended_level = max(0, min(7, current_level + level_shift))

        if recommended_level < current_level:
            reason = f"Effortless mastery (Score: {recent[-1]:.0f}%). Fading scaffold to promote speaking automaticity."
        elif recommended_level > current_level:
            reason = f"Cognitive strain detected (Score: {recent[-1]:.0f}%). Providing targeted scaffolding structure."
        else:
            reason = f"Optimal ZPD flow state (Score: {recent[-1]:.0f}%). Sustaining current scaffolding."

        return PIDScaffoldDecision(
            recommended_level=recommended_level,
            control_signal=round(control_signal, 3),
            p_term=round(p_term, 3),
            i_term=round(i_term, 3),
            d_term=round(d_term, 3),
            reason=reason,
        )

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


class PIDScaffoldDecision:
    """Telemetry and decision record produced by PID Scaffold Controller."""

    def __init__(
        self,
        recommended_level: int,
        control_signal: float,
        p_term: float,
        i_term: float,
        d_term: float,
        reason: str,
    ):
        self.recommended_level = recommended_level
        self.control_signal = control_signal
        self.p_term = p_term
        self.i_term = i_term
        self.d_term = d_term
        self.reason = reason

    def to_dict(self) -> dict:
        return {
            "recommended_level": self.recommended_level,
            "control_signal": self.control_signal,
            "p_term": self.p_term,
            "i_term": self.i_term,
            "d_term": self.d_term,
            "reason": self.reason,
        }
