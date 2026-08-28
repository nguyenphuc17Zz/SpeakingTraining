"""CoachResponseFormatter §43-44."""

from __future__ import annotations

from app.domains.coach.contracts import CoachResponseMode


class CoachResponseFormatter:
    @staticmethod
    def format(answer: str, mode: CoachResponseMode = CoachResponseMode.STANDARD, max_paragraphs: int | None = None) -> str:
        if mode == CoachResponseMode.BRIEF:
            # first 2 sentences / 300 chars
            brief = answer.strip().split("\n\n")[0]
            return brief[:400]
        if mode == CoachResponseMode.DETAILED:
            return answer
        if mode == CoachResponseMode.TEACHING:
            # ensure teaching loop structure
            if "Try" not in answer:
                return answer + "\n\n**Thử ngay:** Hãy làm 1 bài tập tương tự để củng cố."
        # STANDARD
        if max_paragraphs and len(answer.split("\n\n")) > max_paragraphs:
            return "\n\n".join(answer.split("\n\n")[:max_paragraphs])
        return answer
