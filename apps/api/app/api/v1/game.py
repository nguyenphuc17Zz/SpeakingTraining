from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gamification.application.achievement_engine import AchievementEngine
from app.domains.gamification.application.boss_service import BossService
from app.domains.gamification.application.notification_service import GamificationNotificationService
from app.domains.gamification.application.progression_service import ProgressionService
from app.domains.gamification.application.quest_engine import QuestEngine
from app.domains.gamification.application.skill_tree_service import SkillTreeService
from app.domains.gamification.application.streak_service import StreakService
from app.domains.gamification.application.unlock_service import UnlockService
from app.domains.gamification.application.xp_service import XPService
from app.domains.gamification.models import GameSettings
from app.domains.gamification.schemas import (
    AchievementDTO,
    BossAttemptResultDTO,
    BossDTO,
    BossStartResponseDTO,
    GameProfileDTO,
    GameSettingsDTO,
    QuestDTO,
    RewardNotificationDTO,
    SkillTreeOverviewDTO,
    StreakOverviewDTO,
    UnlockableDTO,
    UpdateGameSettingsDTO,
    XPOverviewDTO,
    XPTransactionDTO,
)
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db
from app.shared.errors.exceptions import NotFoundException

router = APIRouter(prefix="/game", tags=["Gamification & RPG"])


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    return user.id


@router.get("/profile", response_model=GameProfileDTO)
async def get_game_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the unified RPG GameProfile for the active learner."""
    service = ProgressionService(db)
    return await service.get_game_profile_dto(user_id)


@router.get("/xp", response_model=XPOverviewDTO)
async def get_xp_overview(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns XP totals, category breakdown, and recent transactions."""
    service = ProgressionService(db)
    return await service.get_xp_overview(user_id)


@router.get("/xp/history", response_model=list[XPTransactionDTO])
async def get_xp_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves paginated immutable XP ledger history for auditing."""
    service = XPService(db)
    txs = await service.get_xp_history(user_id, limit=limit, offset=offset, category=category)
    return [
        XPTransactionDTO(
            id=tx.id,
            amount=tx.amount,
            category=tx.category,
            reason=tx.reason,
            source_type=tx.source_type,
            source_id=tx.source_id,
            created_at=tx.created_at,
            reward_policy_version=tx.reward_policy_version,
        )
        for tx in txs
    ]


@router.get("/quests", response_model=list[QuestDTO])
async def get_quests(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all daily and weekly personalized quests."""
    engine = QuestEngine(db)
    return await engine.get_all_active_quests_dto(user_id)


@router.get("/achievements", response_model=list[AchievementDTO])
async def get_achievements(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves achievement gallery with current progress ratios."""
    engine = AchievementEngine(db)
    return await engine.get_achievements_dto(user_id)


@router.get("/skills", response_model=SkillTreeOverviewDTO)
async def get_skill_tree(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Synthesizes the Japanese Speaking Skill Tree from real LearningEngine data."""
    service = SkillTreeService(db)
    return await service.get_skill_tree_overview(user_id)


@router.get("/unlocks", response_model=list[UnlockableDTO])
async def get_unlockables(
    unlock_type: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns all persona, voice, scenario, and title unlockables."""
    service = UnlockService(db)
    return await service.get_unlocks_dto(user_id, unlock_type=unlock_type)


@router.post("/unlocks/equip-title", response_model=GameProfileDTO)
async def equip_title(
    title: str = Query(..., min_length=1),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Equips an unlocked title to the learner's GameProfile."""
    service = UnlockService(db)
    await service.equip_title(user_id, title)
    prog_service = ProgressionService(db)
    return await prog_service.get_game_profile_dto(user_id)


@router.get("/bosses", response_model=list[BossDTO])
async def get_bosses(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all high-stakes Boss Battle challenges."""
    service = BossService(db)
    return await service.get_bosses_dto(user_id)


@router.post("/bosses/{boss_id}/start", response_model=BossStartResponseDTO)
async def start_boss(
    boss_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Starts a Boss Battle challenge and creates the associated exercise session."""
    service = BossService(db)
    return await service.start_boss_battle(user_id, boss_id)


@router.post("/bosses/{boss_id}/submit", response_model=BossAttemptResultDTO)
async def submit_boss(
    boss_id: str,
    exercise_attempt_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Evaluates boss outcome and awards clear bonuses and titles."""
    service = BossService(db)
    return await service.submit_boss_result(user_id, boss_id, exercise_attempt_id)


@router.get("/notifications", response_model=list[RewardNotificationDTO])
async def get_notifications(
    limit: int = Query(20, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves pending unread reward notifications."""
    service = GamificationNotificationService(db)
    return await service.get_unread_notifications(user_id, limit=limit)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Marks a notification as seen/read."""
    service = GamificationNotificationService(db)
    await service.mark_as_read(user_id, notification_id)
    return {"status": "success", "id": notification_id}


@router.get("/streak", response_model=StreakOverviewDTO)
async def get_streak_overview(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Returns timezone-aware streak tracking and 7-day activity history."""
    service = StreakService(db)
    data = await service.get_streak_overview(user_id)
    return StreakOverviewDTO(**data)


@router.get("/settings", response_model=GameSettingsDTO)
async def get_game_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves learner's gamification preferences."""
    stmt = select(GameSettings).where(GameSettings.user_id == user_id)
    res = await db.execute(stmt)
    settings = res.scalar_one_or_none()
    if not settings:
        settings = GameSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return GameSettingsDTO(
        gamification_enabled=settings.gamification_enabled,
        sound_enabled=settings.sound_enabled,
        animations_enabled=settings.animations_enabled,
        quest_intensity=settings.quest_intensity,
        difficulty_preference=settings.difficulty_preference,
        show_xp_popups=settings.show_xp_popups,
    )


@router.put("/settings", response_model=GameSettingsDTO)
async def update_game_settings(
    payload: UpdateGameSettingsDTO,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Updates learner's gamification preferences."""
    stmt = select(GameSettings).where(GameSettings.user_id == user_id)
    res = await db.execute(stmt)
    settings = res.scalar_one_or_none()
    if not settings:
        settings = GameSettings(user_id=user_id)
        db.add(settings)

    if payload.gamification_enabled is not None:
        settings.gamification_enabled = payload.gamification_enabled
    if payload.sound_enabled is not None:
        settings.sound_enabled = payload.sound_enabled
    if payload.animations_enabled is not None:
        settings.animations_enabled = payload.animations_enabled
    if payload.quest_intensity is not None:
        settings.quest_intensity = payload.quest_intensity
    if payload.difficulty_preference is not None:
        settings.difficulty_preference = payload.difficulty_preference
    if payload.show_xp_popups is not None:
        settings.show_xp_popups = payload.show_xp_popups

    await db.commit()
    await db.refresh(settings)

    return GameSettingsDTO(
        gamification_enabled=settings.gamification_enabled,
        sound_enabled=settings.sound_enabled,
        animations_enabled=settings.animations_enabled,
        quest_intensity=settings.quest_intensity,
        difficulty_preference=settings.difficulty_preference,
        show_xp_popups=settings.show_xp_popups,
    )
