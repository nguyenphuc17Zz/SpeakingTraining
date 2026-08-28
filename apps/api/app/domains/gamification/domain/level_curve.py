import math
from typing import Any

from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import RankTier


class LevelCurve:
    """
    Centralized, deterministic mathematical level curve.
    Uses a smooth polynomial formula:
      xp_for_level(L) = BASE_XP * (L - 1) ^ EXPONENT
    Predictable, tunable, avoids absurd exponential roadblocks while keeping high levels meaningful.
    """

    @classmethod
    def total_xp_for_level(cls, level: int) -> int:
        """Total cumulative XP required from Level 1 to reach `level`."""
        if level <= 1:
            return 0
        exponent = BALANCE_CONFIG.LEVEL_CURVE_EXPONENT
        base = BALANCE_CONFIG.LEVEL_CURVE_BASE_XP
        # Cumulative sum of per-level delta
        total = 0
        for lvl in range(1, level):
            delta = int(base * math.pow(lvl, exponent - 0.5) + (lvl * 50))
            total += delta
        return total

    @classmethod
    def xp_required_for_next_level(cls, current_level: int) -> int:
        """XP needed to advance from `current_level` to `current_level + 1`."""
        exponent = BALANCE_CONFIG.LEVEL_CURVE_EXPONENT
        base = BALANCE_CONFIG.LEVEL_CURVE_BASE_XP
        return int(base * math.pow(current_level, exponent - 0.5) + (current_level * 50))

    @classmethod
    def level_from_total_xp(cls, total_xp: int) -> int:
        """Calculates current RPG level (1..MAX_LEVEL) from total cumulative XP."""
        if total_xp <= 0:
            return 1
        
        # Iterative step-up (fast since MAX_LEVEL <= 100)
        accumulated = 0
        level = 1
        while level < BALANCE_CONFIG.MAX_LEVEL:
            needed = cls.xp_required_for_next_level(level)
            if total_xp < accumulated + needed:
                break
            accumulated += needed
            level += 1
        return level

    @classmethod
    def level_progress_info(cls, total_xp: int) -> dict[str, Any]:
        """
        Returns structured level progress:
          current_level, total_xp, current_level_xp, next_level_xp, progress_ratio, is_max_level
        """
        level = cls.level_from_total_xp(total_xp)
        if level >= BALANCE_CONFIG.MAX_LEVEL:
            return {
                "level": level,
                "total_xp": total_xp,
                "current_level_xp": 0,
                "next_level_xp": 0,
                "progress_ratio": 1.0,
                "is_max_level": True,
            }

        prev_level_total = cls.total_xp_for_level(level)
        next_level_cost = cls.xp_required_for_next_level(level)
        xp_in_current_level = max(0, total_xp - prev_level_total)
        ratio = min(1.0, max(0.0, xp_in_current_level / max(1, next_level_cost)))

        return {
            "level": level,
            "total_xp": total_xp,
            "current_level_xp": xp_in_current_level,
            "next_level_xp": next_level_cost,
            "progress_ratio": round(ratio, 4),
            "is_max_level": False,
        }

    @classmethod
    def rank_from_level(cls, level: int) -> RankTier:
        """Derives learner game progression rank tier from RPG level."""
        if level < 5:
            return RankTier.BEGINNER
        elif level < 10:
            return RankTier.BRONZE
        elif level < 20:
            return RankTier.SILVER
        elif level < 35:
            return RankTier.GOLD
        elif level < 50:
            return RankTier.PLATINUM
        elif level < 70:
            return RankTier.DIAMOND
        else:
            return RankTier.MASTER
