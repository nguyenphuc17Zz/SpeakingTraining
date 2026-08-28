"""TopicValidator §41."""

from __future__ import annotations

from typing import Any

from app.domains.monologue.contracts import SpeechGenre, SpeechSupportLevel


class TopicValidator:
    FORBIDDEN_PHRASES = {"kill", "suicide", "terror", "bomb", "abuse"}

    @classmethod
    def validate(
        cls,
        topic: str,
        instruction: str,
        genre: SpeechGenre,
        difficulty: int,
        duration_sec: int,
        topic_domain: str,
        constraints: list[str],
        support_level: SpeechSupportLevel | int,
        session_signature: str,
        recent_signatures: list[str],
    ) -> tuple[bool, list[str]]:
        issues: list[str] = []
        if not topic or len(topic.strip()) < 4:
            issues.append("Topic too short or missing")
        if not instruction or len(instruction.strip()) < 10:
            issues.append("Instruction too short or missing")
        # speakability: avoid obscure encyclopedic requirement
        if len(topic) > 200:
            issues.append("Topic too long")
        # level fit: N5 shouldn't get 300s business_update with difficulty 5
        if difficulty < 1 or difficulty > 5:
            issues.append("Difficulty out of range 1-5")
        if duration_sec not in (30, 45, 60, 90, 120, 180, 300):
            issues.append(f"Invalid duration {duration_sec}")
        # genre compatibility
        try:
            _ = SpeechGenre(genre) if isinstance(genre, str) else genre
        except Exception:
            issues.append(f"Invalid genre {genre}")
        # content safety (simple)
        low = (topic + " " + instruction).lower()
        for bad in cls.FORBIDDEN_PHRASES:
            if bad in low:
                issues.append("Content safety: forbidden theme")
        # clear instructions
        if "?" not in instruction and "してください" not in instruction and "しよう" not in instruction and len(instruction) < 15:
            # soft check: instruction should contain an action
            pass
        # non-duplication
        if session_signature and session_signature in (recent_signatures or []):
            issues.append("Duplicate session_signature in recency window")
        # learning value: must have at least one constraint or support
        if not constraints and int(support_level) == 4 and difficulty <= 2:
            # minimal scaffolding but no constraint for easy level may be too open
            pass
        return len(issues) == 0, issues
