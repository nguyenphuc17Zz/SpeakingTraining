import pytest
from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType, XPCategory
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.domain.level_curve import LevelCurve
from app.domains.gamification.domain.reward_policy import RewardPolicy
from app.domains.gamification.application.xp_service import XPService
from app.infrastructure.database.session import AsyncSessionLocal


def test_level_curve_math():
    """Verify LevelCurve calculates deterministic, predictable level boundaries."""
    assert LevelCurve.level_from_total_xp(0) == 1
    assert LevelCurve.level_from_total_xp(100) == 1

    # Level 2 threshold
    cost_to_l2 = LevelCurve.xp_required_for_next_level(1)
    assert cost_to_l2 > 0
    assert LevelCurve.level_from_total_xp(cost_to_l2) == 2
    assert LevelCurve.level_from_total_xp(cost_to_l2 - 1) == 1

    # Check progress info
    info = LevelCurve.level_progress_info(150)
    assert info["level"] == 1
    assert info["current_level_xp"] == 150
    assert 0.0 < info["progress_ratio"] < 1.0


def test_reward_policy_deterministic_values():
    """Verify RewardPolicy properly applies difficulty, independence, and diminishing factors."""
    event = GameEvent(
        user_id="test_user",
        type=GameEventType.EXERCISE_COMPLETED,
        source=GameEventSource.LEARNING,
        source_id="ex_1",
        metadata={
            "difficulty": "hard",
            "score": 95.0,
            "independence_level": "independent",
            "mastery_delta": 0.15,
        },
    )

    reward = RewardPolicy.calculate_reward(event, repetition_count_today=0)
    assert reward.category == XPCategory.EXERCISE
    assert reward.base_xp == BALANCE_CONFIG.XP_EXERCISE_HARD
    # Hard base (100) * 1.15 score multiplier + 15 bonus = ~130 XP
    assert reward.xp_amount >= 120

    # Test diminishing returns on repetition
    rep_reward = RewardPolicy.calculate_reward(event, repetition_count_today=3)
    assert rep_reward.xp_amount < reward.xp_amount


from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_xp_ledger_and_profile_reconciliation(db_session: AsyncSession):
    """Verify immutable ledger appends rows and reconciles cached balance."""
    xp_service = XPService(db_session)
    user_id = "test_user_xp_ledger"

    # 1. Initial Profile
    profile = await xp_service.get_or_create_profile(user_id)
    initial_xp = profile.total_xp

    # 2. Grant XP
    tx, did_lvl, old_lvl, new_lvl = await xp_service.grant_xp(
        user_id=user_id,
        amount=500,
        category=XPCategory.EXERCISE,
        reason="Test Exercise Complete",
        source_type="learning",
        source_id="test_attempt_1",
    )
    assert tx.amount == 500
    assert profile.total_xp == initial_xp + 500

    # 3. Sum ledger directly
    ledger_sum = await xp_service.get_total_xp_from_ledger(user_id)
    assert ledger_sum >= 500

    # 4. Reconcile
    reconciled_prof = await xp_service.reconcile_profile_xp(user_id)
    assert reconciled_prof.total_xp == ledger_sum
