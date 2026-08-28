import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.application.achievement_engine import AchievementEngine
from app.domains.gamification.application.skill_tree_service import SkillTreeService
from app.domains.gamification.application.boss_service import BossService


@pytest.mark.asyncio
async def test_achievement_engine_evaluation(db_session: AsyncSession):
    """Verify achievements evaluate declarative conditions and return DTOs."""
    ach_engine = AchievementEngine(db_session)
    user_id = "test_user_ach_1"

    dtos = await ach_engine.get_achievements_dto(user_id)
    assert len(dtos) >= 5

    # Evaluate on event
    event = GameEvent(
        user_id=user_id,
        type=GameEventType.CONVERSATION_COMPLETED,
        source=GameEventSource.CONVERSATION,
        source_id="conv_ach_test_1",
        metadata={"duration_seconds": 300},
    )
    unlocked = await ach_engine.evaluate_achievements(user_id, event)
    assert isinstance(unlocked, list)


@pytest.mark.asyncio
async def test_skill_tree_overview(db_session: AsyncSession):
    """Verify skill tree overview compiles branches and node statuses from Learning Engine."""
    skill_service = SkillTreeService(db_session)
    user_id = "test_user_skill_1"

    overview = await skill_service.get_skill_tree_overview(user_id)
    assert len(overview.categories) == 4
    assert len(overview.nodes) >= 8
    assert all(hasattr(n, "status") for n in overview.nodes)


@pytest.mark.asyncio
async def test_boss_service_flow(db_session: AsyncSession):
    """Verify boss battle retrieval, starting challenge, and evaluation."""
    from app.domains.gamification.application.xp_service import XPService
    from app.domains.gamification.domain.contracts import XPCategory

    xp_service = XPService(db_session)
    boss_service = BossService(db_session)
    user_id = "test_user_boss_1"

    # Grant XP to reach Level 5
    await xp_service.grant_xp(
        user_id=user_id,
        amount=2500,
        category=XPCategory.SPECIAL,
        reason="Level up for boss test",
        source_type="system",
        source_id="sys_lvl",
    )

    bosses = await boss_service.get_bosses_dto(user_id)
    assert len(bosses) >= 1

    first_boss = bosses[0]
    assert first_boss.is_unlocked is True

    # Start challenge
    start_res = await boss_service.start_boss_battle(user_id, first_boss.id)
    assert start_res.exercise_id is not None
    assert start_res.boss_id == first_boss.id
