from app.domains.conversation_intelligence.contracts import (
    ContextNote,
    CorrectionCategory,
    CorrectionItem,
    CorrectionSeverity,
)


class ContextAnalyzer:
    """Evaluates situational appropriateness, persona role adherence, and formality."""

    @staticmethod
    def evaluate_context_appropriateness(
        persona_role: str,
        user_transcript: str,
        corrections: list[CorrectionItem],
    ) -> tuple[list[ContextNote], list[CorrectionItem]]:
        notes: list[ContextNote] = []
        is_formal_partner = any(
            role in persona_role.lower()
            for role in ["teacher", "sensei", "interviewer", "boss", "senior", "tanaka", "formal"]
        )

        # Check for overly casual slang when speaking to interviewer/teacher
        if is_formal_partner:
            casual_endings = ["だよ", "だね", "じゃん", "どうも", "うん"]
            if any(user_transcript.strip().endswith(ending) for ending in casual_endings):
                notes.append(
                    ContextNote(
                        persona_role=persona_role,
                        formality_level="too_casual",
                        observation=f"Đối tác là '{persona_role}', nên ưu tiên sử dụng thể lịch sự (Desu/Masu) hoặc Keigo thay vì Tameguchi.",
                    )
                )

        return notes, corrections
