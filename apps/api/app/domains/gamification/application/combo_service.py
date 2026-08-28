from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class SessionComboState(BaseModel):
    user_id: str
    session_id: str
    current_combo: int = 0
    max_combo: int = 0
    last_action_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComboService:
    """
    Tracks in-session consecutive meaningful learning successes (combos).
    Designed to encourage sustained active speaking without punitive pressure on natural mistakes.
    """
    _combos: dict[str, SessionComboState] = {}

    @classmethod
    def record_success(cls, user_id: str, session_id: str) -> dict[str, Any]:
        """Increments current session combo upon a successful learning turn/exercise."""
        key = f"{user_id}:{session_id}"
        state = cls._combos.get(key)
        now = datetime.now(timezone.utc)

        if not state:
            state = SessionComboState(user_id=user_id, session_id=session_id)
            cls._combos[key] = state

        state.current_combo += 1
        state.max_combo = max(state.max_combo, state.current_combo)
        state.last_action_at = now

        combo_mult = min(2.0, 1.0 + (state.current_combo * 0.10))

        return {
            "current_combo": state.current_combo,
            "max_combo": state.max_combo,
            "multiplier": round(combo_mult, 2),
        }

    @classmethod
    def get_combo(cls, user_id: str, session_id: str) -> int:
        key = f"{user_id}:{session_id}"
        state = cls._combos.get(key)
        return state.current_combo if state else 0

    @classmethod
    def reset_combo(cls, user_id: str, session_id: str) -> None:
        key = f"{user_id}:{session_id}"
        if key in cls._combos:
            del cls._combos[key]
