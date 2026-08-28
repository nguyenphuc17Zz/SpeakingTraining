from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.models import (
    GameProfile,
    UnlockableDefinition,
    UserAchievement,
    UserUnlock,
)
from app.domains.gamification.schemas import UnlockableDTO
from app.shared.errors.exceptions import NotFoundException, ValidationException


class UnlockService:
    """
    Evaluates progression milestones and manages user cosmetics, titles, personas, and voice unlocks.
    Never locks core AI models, essential accessibility, or foundational learning features.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_unlocks(self, user_id: str) -> list[dict[str, Any]]:
        """
        Checks all unlockable definitions against user level & achievements.
        Returns a list of newly unlocked items.
        """
        # Fetch profile
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        current_level = profile.level if profile else 1

        # Fetch definitions
        defs_stmt = select(UnlockableDefinition)
        defs_res = await self.db.execute(defs_stmt)
        definitions = list(defs_res.scalars().all())

        # Fetch current user unlocks
        uu_stmt = select(UserUnlock).where(UserUnlock.user_id == user_id)
        uu_res = await self.db.execute(uu_stmt)
        unlocked_ids = {uu.unlockable_id for uu in uu_res.scalars().all()}

        newly_unlocked = []
        for d in definitions:
            if d.id in unlocked_ids:
                continue

            # Level requirement condition
            if current_level >= d.level_required:
                uu = UserUnlock(
                    user_id=user_id,
                    unlockable_id=d.id,
                    unlocked_at=datetime.now(timezone.utc),
                    is_equipped=False,
                )
                self.db.add(uu)
                newly_unlocked.append({
                    "unlockable_id": d.id,
                    "key": d.key,
                    "title": d.title,
                    "unlock_type": d.unlock_type,
                    "description": d.description,
                })
                logger.info(f"[UnlockService] User {user_id} unlocked {d.unlock_type} '{d.title}'!")

        if newly_unlocked:
            await self.db.commit()

        return newly_unlocked

    async def get_unlocks_dto(self, user_id: str, unlock_type: str | None = None) -> list[UnlockableDTO]:
        """Returns structured list of unlockables with unlock and equip state."""
        defs_stmt = select(UnlockableDefinition).order_by(UnlockableDefinition.level_required.asc())
        if unlock_type:
            defs_stmt = defs_stmt.where(UnlockableDefinition.unlock_type == unlock_type)
        defs_res = await self.db.execute(defs_stmt)
        definitions = list(defs_res.scalars().all())

        uu_stmt = select(UserUnlock).where(UserUnlock.user_id == user_id)
        uu_res = await self.db.execute(uu_stmt)
        user_unlocks = {uu.unlockable_id: uu for uu in uu_res.scalars().all()}

        dtos = []
        for d in definitions:
            uu = user_unlocks.get(d.id)
            is_unlocked = uu is not None
            dtos.append(
                UnlockableDTO(
                    id=d.id,
                    key=d.key,
                    unlock_type=d.unlock_type,
                    title=d.title,
                    description=d.description,
                    level_required=d.level_required,
                    is_unlocked=is_unlocked,
                    unlocked_at=uu.unlocked_at if uu else None,
                    is_equipped=uu.is_equipped if uu else False,
                    asset_reference=d.asset_reference,
                )
            )
        return dtos

    async def equip_title(self, user_id: str, title_text: str) -> GameProfile:
        """Equips an unlocked title onto the user's GameProfile."""
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        if not profile:
            raise NotFoundException("GameProfile not found.")

        profile.current_title = title_text
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
