import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GameBalanceConfig:
    """
    Centralized game economy configuration.
    Single source of truth for XP values, multipliers, caps, level curves, and reward policies.
    """
    # Base XP Values
    XP_EXERCISE_EASY: int = 30
    XP_EXERCISE_NORMAL: int = 60
    XP_EXERCISE_HARD: int = 100
    XP_EXERCISE_CHALLENGE: int = 150

    XP_CONVERSATION_SHORT: int = 40      # < 5 mins
    XP_CONVERSATION_MEDIUM: int = 90     # 5 - 15 mins
    XP_CONVERSATION_LONG: int = 150      # > 15 mins

    XP_PRONUNCIATION_ATTEMPT: int = 20
    XP_PRONUNCIATION_IMPROVEMENT_BONUS: int = 50

    XP_SHADOWING_SEGMENT: int = 25
    XP_SHADOWING_VIDEO_COMPLETE: int = 120

    XP_LEARNING_ITEM_MASTERED: int = 200
    XP_LEARNING_ITEM_IMPROVED: int = 80
    XP_LEARNING_ITEM_MAINTAINED: int = 30

    XP_DAILY_PLAN_COMPLETED: int = 250
    XP_DAILY_QUEST_DEFAULT: int = 200
    XP_WEEKLY_QUEST_DEFAULT: int = 500

    XP_BOSS_PASS_NORMAL: int = 500
    XP_BOSS_PASS_HARD: int = 800
    XP_BOSS_PASS_EXTREME: int = 1200
    XP_BOSS_IMPROVEMENT_BONUS: int = 150

    XP_STREAK_MILESTONE_7D: int = 300
    XP_STREAK_MILESTONE_30D: int = 1000
    XP_STREAK_MILESTONE_100D: int = 3000

    # Independence Multipliers
    MULT_INDEPENDENT: float = 1.0
    MULT_ASSISTED_HINT: float = 0.70
    MULT_RETRY_SUCCESS: float = 0.50
    MULT_SCAFFOLDED: float = 0.30

    # Daily XP Caps from Repetitive Actions (to prevent abuse without blocking mastery)
    DAILY_CAP_EXERCISE_REPETITIVE: int = 600
    DAILY_CAP_PRONUNCIATION: int = 350
    DAILY_CAP_SHADOWING: int = 400

    # Diminishing Returns Multipliers on exact duplicate target attempts in a single day
    DIMINISHING_RATES: list[float] = field(default_factory=lambda: [1.0, 0.70, 0.45, 0.25, 0.10])

    # Level Curve Coefficients (Polynomial formula: XP = a * Level^b + c * Level)
    LEVEL_CURVE_EXPONENT: float = 1.65
    LEVEL_CURVE_BASE_XP: int = 300
    MAX_LEVEL: int = 100

    # Skill Points awarded per level
    SKILL_POINTS_PER_LEVEL: int = 1

    # Streak Qualification Thresholds
    STREAK_MIN_SPEAKING_MINUTES: int = 3
    STREAK_MIN_EXERCISES: int = 1
    STREAK_MIN_PRONUNCIATION_ATTEMPTS: int = 2
    STREAK_MIN_SHADOWING_SEGMENTS: int = 2

    # Reward Policy Version
    REWARD_POLICY_VERSION: str = "1.0.0"
    QUEST_DEFINITION_VERSION: str = "1.0.0"
    ACHIEVEMENT_DEFINITION_VERSION: str = "1.0.0"


BALANCE_CONFIG = GameBalanceConfig()
