from typing import Protocol

from pydantic import BaseModel


class Quest(BaseModel):
    id: str
    title: str
    description: str
    xp_reward: int
    is_completed: bool = False
    progress: float = 0.0  # 0.0 to 1.0


class UserGamificationStats(BaseModel):
    user_id: str
    level: int
    current_xp: int
    next_level_xp: int
    streak_days: int
    total_speaking_minutes: int
    active_quests: list[Quest] = []


class GamificationEngine(Protocol):
    """Protocol for Japanese RPG leveling, streaks, daily missions, and XP calculations."""

    async def get_user_stats(self, user_id: str) -> UserGamificationStats:
        ...

    async def award_speaking_xp(self, user_id: str, minutes_spoken: int, accuracy: float) -> UserGamificationStats:
        ...
