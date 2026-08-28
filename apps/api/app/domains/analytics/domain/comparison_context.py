from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComparisonContext:
    session_type: str = "conversation"  # conversation, roleplay, interview, drill, shadowing
    difficulty_band: str = "normal"      # beginner, normal, advanced, extreme
    persona_category: str | None = None  # teacher, casual_friend, interviewer, customer
    mode: str = "conversation"           # conversation, coaching
    duration_band: str = "standard"      # short (<3m), standard (3-15m), extended (>15m)

    @classmethod
    def from_session_metadata(
        cls,
        mode: str = "conversation",
        difficulty: str = "normal",
        persona_category: str | None = None,
        duration_seconds: int | None = None,
        session_type: str = "conversation",
    ) -> "ComparisonContext":
        duration_band = "standard"
        if duration_seconds is not None:
            if duration_seconds < 180:
                duration_band = "short"
            elif duration_seconds > 900:
                duration_band = "extended"

        return cls(
            session_type=session_type,
            difficulty_band=difficulty.lower() if difficulty else "normal",
            persona_category=persona_category.lower() if persona_category else None,
            mode=mode.lower() if mode else "conversation",
            duration_band=duration_band,
        )

    def is_comparable_to(self, other: "ComparisonContext", strict: bool = False) -> bool:
        """
        Determines if two sessions are fair to compare against each other.
        In loose mode (default): must match session_type and difficulty_band.
        In strict mode: also matches persona_category and duration_band.
        """
        if self.session_type != other.session_type:
            return False
        if self.difficulty_band != other.difficulty_band:
            return False
        if strict:
            if self.mode != other.mode:
                return False
            if self.duration_band != other.duration_band:
                return False
            if self.persona_category and other.persona_category:
                if self.persona_category != other.persona_category:
                    return False
        return True
