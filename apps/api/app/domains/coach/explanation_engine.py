"""CoachExplanationEngine §53 + Teaching loop §54."""

from __future__ import annotations

from typing import Any


class CoachExplanationEngine:
    """Deterministic explanation helper — produces What/Why/What-to-do/Try structure."""

    @staticmethod
    def format_error_explanation(
        what_happened: str,
        why: str,
        what_to_do: str,
        try_prompt: str,
        evidence: list[dict[str, Any]] | None = None,
    ) -> str:
        lines = [
            f"**Chuyện gì xảy ra:** {what_happened}",
            f"**Tại sao:** {why}",
            f"**Làm gì tiếp:** {what_to_do}",
            f"**Thử ngay:** {try_prompt}",
        ]
        if evidence:
            lines.append("\n**Bằng chứng:**")
            for e in evidence[:3]:
                metric = e.get("metric", "metric")
                val = e.get("value", "?")
                n = e.get("sample_count", "?")
                lines.append(f"- {metric}: {val} (n={n}, source={e.get('source','engine')})")
        return "\n\n".join(lines)

    @staticmethod
    def micro_lesson_structure(problem: str, why: str, example: str, try_prompt: str, feedback: str = "") -> dict[str, str]:
        return {
            "problem": problem,
            "why": why,
            "example": example,
            "try": try_prompt,
            "feedback": feedback,
        }
