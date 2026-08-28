import math
from typing import Any
from pydantic import BaseModel, Field

from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import GameEventType, XPCategory
from app.domains.gamification.domain.game_event import GameEvent


class RewardCalculationResult(BaseModel):
    xp_amount: int
    category: XPCategory
    reason: str
    base_xp: int
    multiplier: float
    diminishing_factor: float
    bonus_xp: int
    policy_version: str = BALANCE_CONFIG.REWARD_POLICY_VERSION
    metadata: dict[str, Any] = Field(default_factory=dict)


class RewardPolicy:
    """
    Deterministic rule engine that calculates XP from normalized GameEvents.
    AI does not decide XP rewards directly — rewards are bounded, formulaic, and transparent.
    """

    @classmethod
    def calculate_reward(
        cls,
        event: GameEvent,
        repetition_count_today: int = 0,
        daily_category_xp_so_far: int = 0,
    ) -> RewardCalculationResult:
        """
        Calculates deterministic XP and category for a given GameEvent.
        Applies difficulty multipliers, independence weighting, diminishing returns, and daily caps.
        """
        meta = event.metadata
        event_type = event.type

        # 1. Base XP & Category by Event Type
        base_xp = 0
        category = XPCategory.SPECIAL
        reason = f"Activity: {event_type.value}"

        if event_type == GameEventType.EXERCISE_COMPLETED:
            category = XPCategory.EXERCISE
            difficulty = meta.get("difficulty", "normal").lower()
            if difficulty == "easy":
                base_xp = BALANCE_CONFIG.XP_EXERCISE_EASY
            elif difficulty == "hard":
                base_xp = BALANCE_CONFIG.XP_EXERCISE_HARD
            elif difficulty == "challenge":
                base_xp = BALANCE_CONFIG.XP_EXERCISE_CHALLENGE
            else:
                base_xp = BALANCE_CONFIG.XP_EXERCISE_NORMAL
            reason = f"Completed {difficulty.capitalize()} Exercise"

        elif event_type == GameEventType.CONVERSATION_COMPLETED:
            category = XPCategory.CONVERSATION
            duration_secs = meta.get("duration_seconds", 0)
            duration_mins = duration_secs / 60.0
            if duration_mins < 5.0:
                base_xp = BALANCE_CONFIG.XP_CONVERSATION_SHORT
            elif duration_mins <= 15.0:
                base_xp = BALANCE_CONFIG.XP_CONVERSATION_MEDIUM
            else:
                base_xp = BALANCE_CONFIG.XP_CONVERSATION_LONG
            reason = f"Completed {round(duration_mins, 1)}m Spoken Conversation"

        elif event_type == GameEventType.PRONUNCIATION_ATTEMPTED:
            category = XPCategory.PRONUNCIATION
            base_xp = BALANCE_CONFIG.XP_PRONUNCIATION_ATTEMPT
            reason = "Pronunciation Practice Attempt"

        elif event_type == GameEventType.PRONUNCIATION_IMPROVED:
            category = XPCategory.PRONUNCIATION
            base_xp = BALANCE_CONFIG.XP_PRONUNCIATION_IMPROVEMENT_BONUS
            delta = meta.get("score_delta", 0)
            reason = f"Pronunciation Improvement (+{round(delta, 1)} pts)"

        elif event_type == GameEventType.SHADOWING_COMPLETED:
            category = XPCategory.SHADOWING
            if meta.get("is_full_video", False):
                base_xp = BALANCE_CONFIG.XP_SHADOWING_VIDEO_COMPLETE
                reason = "Completed Video Shadowing Session"
            else:
                base_xp = BALANCE_CONFIG.XP_SHADOWING_SEGMENT
                reason = "Shadowed Video Segment"

        elif event_type == GameEventType.LEARNING_ITEM_MASTERED:
            category = XPCategory.MASTERY
            base_xp = BALANCE_CONFIG.XP_LEARNING_ITEM_MASTERED
            item_title = meta.get("item_title", "Language Point")
            reason = f"Mastered Item: {item_title}"

        elif event_type == GameEventType.LEARNING_ITEM_IMPROVED:
            category = XPCategory.MASTERY
            base_xp = BALANCE_CONFIG.XP_LEARNING_ITEM_IMPROVED
            item_title = meta.get("item_title", "Language Point")
            reason = f"Significant Mastery Growth: {item_title}"

        elif event_type == GameEventType.DAILY_PLAN_COMPLETED:
            category = XPCategory.QUEST
            base_xp = BALANCE_CONFIG.XP_DAILY_PLAN_COMPLETED
            reason = "Completed All Daily Learning Plan Goals"

        elif event_type == GameEventType.BOSS_CLEARED:
            category = XPCategory.BOSS
            boss_diff = meta.get("difficulty", "normal").lower()
            if boss_diff == "hard":
                base_xp = BALANCE_CONFIG.XP_BOSS_PASS_HARD
            elif boss_diff == "extreme":
                base_xp = BALANCE_CONFIG.XP_BOSS_PASS_EXTREME
            else:
                base_xp = BALANCE_CONFIG.XP_BOSS_PASS_NORMAL
            boss_name = meta.get("boss_name", "Boss Challenge")
            reason = f"Defeated Boss: {boss_name} ({boss_diff.capitalize()})"

        elif event_type == GameEventType.REVIEW_COMPLETED:
            category = XPCategory.EXERCISE
            base_xp = BALANCE_CONFIG.XP_EXERCISE_NORMAL
            reason = "Spaced Repetition Review Completed"

        else:
            base_xp = 20
            category = XPCategory.SPECIAL
            reason = f"Learning Activity: {event_type.value}"

        # 2. Multipliers: Independence & Quality Score
        multiplier = 1.0

        # Independence level
        indep = str(meta.get("independence_level", "independent")).lower()
        if indep == "assisted_hint":
            multiplier *= BALANCE_CONFIG.MULT_ASSISTED_HINT
        elif indep == "retry_success":
            multiplier *= BALANCE_CONFIG.MULT_RETRY_SUCCESS
        elif indep == "scaffolded":
            multiplier *= BALANCE_CONFIG.MULT_SCAFFOLDED
        else:
            multiplier *= BALANCE_CONFIG.MULT_INDEPENDENT

        # Quality score modifier (e.g. score >= 90 adds +15% bonus, score < 60 reduces by 20%)
        score = meta.get("score")
        if score is not None and isinstance(score, (int, float)):
            if score >= 90:
                multiplier *= 1.15
            elif score >= 75:
                multiplier *= 1.00
            elif score >= 60:
                multiplier *= 0.85
            else:
                multiplier *= 0.70

        # 3. Diminishing returns on repetitive actions (same target/exercise within a single day)
        diminishing_rates = BALANCE_CONFIG.DIMINISHING_RATES
        if repetition_count_today < len(diminishing_rates):
            diminishing_factor = diminishing_rates[repetition_count_today]
        else:
            diminishing_factor = diminishing_rates[-1]

        # 4. Mastery improvement bonuses
        bonus_xp = 0
        mastery_delta = meta.get("mastery_delta", 0.0)
        if isinstance(mastery_delta, (int, float)) and mastery_delta > 0.08:
            bonus_xp += int(mastery_delta * 100)  # e.g., +0.15 delta -> +15 bonus XP

        # 5. Calculate preliminary amount
        calculated_xp = int((base_xp * multiplier * diminishing_factor) + bonus_xp)
        calculated_xp = max(5, calculated_xp)  # Always grant minimum 5 XP for real effort

        # 6. Apply Daily Caps per category (soft ceiling)
        if category == XPCategory.EXERCISE and daily_category_xp_so_far >= BALANCE_CONFIG.DAILY_CAP_EXERCISE_REPETITIVE:
            calculated_xp = max(5, int(calculated_xp * 0.20))
        elif category == XPCategory.PRONUNCIATION and daily_category_xp_so_far >= BALANCE_CONFIG.DAILY_CAP_PRONUNCIATION:
            calculated_xp = max(5, int(calculated_xp * 0.20))
        elif category == XPCategory.SHADOWING and daily_category_xp_so_far >= BALANCE_CONFIG.DAILY_CAP_SHADOWING:
            calculated_xp = max(5, int(calculated_xp * 0.20))

        return RewardCalculationResult(
            xp_amount=calculated_xp,
            category=category,
            reason=reason,
            base_xp=base_xp,
            multiplier=round(multiplier, 3),
            diminishing_factor=round(diminishing_factor, 2),
            bonus_xp=bonus_xp,
            policy_version=BALANCE_CONFIG.REWARD_POLICY_VERSION,
            metadata={
                "source_type": event.source.value,
                "source_id": event.source_id,
                "repetition_count": repetition_count_today,
            },
        )
