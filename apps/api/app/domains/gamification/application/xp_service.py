from datetime import datetime, timezone
from typing import Any
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import XPCategory
from app.domains.gamification.domain.level_curve import LevelCurve
from app.domains.gamification.models import GameProfile, XPTransaction
from app.shared.errors.exceptions import NotFoundException, ValidationException


class XPService:
    """
    Manages the immutable XP transaction ledger and maintains consistency with the GameProfile cache.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_profile(self, user_id: str) -> GameProfile:
        """Retrieves or initializes the GameProfile for a user."""
        stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        res = await self.db.execute(stmt)
        profile = res.scalar_one_or_none()

        if not profile:
            profile = GameProfile(
                user_id=user_id,
                total_xp=0,
                level=1,
                rank=LevelCurve.rank_from_level(1).value,
                current_streak=0,
                longest_streak=0,
                skill_points=0,
                streak_freezes_available=1,
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            logger.info(f"[XPService] Created initial GameProfile for user {user_id}")

        return profile

    async def grant_xp(
        self,
        user_id: str,
        amount: int,
        category: XPCategory | str,
        reason: str,
        source_type: str,
        source_id: str,
        event_id: str | None = None,
        policy_version: str = BALANCE_CONFIG.REWARD_POLICY_VERSION,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[XPTransaction, bool, int, int]:
        """
        Appends an immutable XP transaction, updates GameProfile cache, and checks for level-up.
        Returns: (transaction, did_level_up, old_level, new_level)
        """
        if amount == 0:
            raise ValidationException("XP amount cannot be zero.")

        cat_str = category.value if isinstance(category, XPCategory) else str(category)

        # 1. Append immutable transaction row
        tx = XPTransaction(
            user_id=user_id,
            amount=amount,
            category=cat_str,
            reason=reason,
            event_id=event_id,
            source_type=source_type,
            source_id=source_id,
            reward_policy_version=policy_version,
            meta_json=metadata,
        )
        self.db.add(tx)

        # 2. Update GameProfile
        profile = await self.get_or_create_profile(user_id)
        old_xp = profile.total_xp
        old_level = profile.level

        new_xp = max(0, old_xp + amount)
        new_level = LevelCurve.level_from_total_xp(new_xp)
        new_rank = LevelCurve.rank_from_level(new_level).value

        did_level_up = new_level > old_level
        if did_level_up:
            level_diff = new_level - old_level
            profile.skill_points += (level_diff * BALANCE_CONFIG.SKILL_POINTS_PER_LEVEL)
            logger.info(f"[XPService] User {user_id} leveled up! {old_level} -> {new_level}")

        profile.total_xp = new_xp
        profile.level = new_level
        profile.rank = new_rank

        await self.db.commit()
        await self.db.refresh(tx)
        await self.db.refresh(profile)

        return tx, did_level_up, old_level, new_level

    async def get_total_xp_from_ledger(self, user_id: str) -> int:
        """Computes true total XP by summing all immutable ledger transactions."""
        stmt = select(func.coalesce(func.sum(XPTransaction.amount), 0)).where(XPTransaction.user_id == user_id)
        res = await self.db.execute(stmt)
        return int(res.scalar() or 0)

    async def reconcile_profile_xp(self, user_id: str) -> GameProfile:
        """Audits and reconciles cached GameProfile with the immutable ledger truth."""
        ledger_total = await self.get_total_xp_from_ledger(user_id)
        profile = await self.get_or_create_profile(user_id)

        if profile.total_xp != ledger_total:
            logger.warning(
                f"[XPService] Profile XP discrepancy for {user_id}: cache={profile.total_xp}, ledger={ledger_total}. Reconciling."
            )
            profile.total_xp = ledger_total
            profile.level = LevelCurve.level_from_total_xp(ledger_total)
            profile.rank = LevelCurve.rank_from_level(profile.level).value
            await self.db.commit()
            await self.db.refresh(profile)

        return profile

    async def get_xp_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
    ) -> list[XPTransaction]:
        """Retrieves user XP ledger history."""
        stmt = select(XPTransaction).where(XPTransaction.user_id == user_id)
        if category:
            stmt = stmt.where(XPTransaction.category == category)
        stmt = stmt.order_by(desc(XPTransaction.created_at)).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_category_breakdown(self, user_id: str) -> dict[str, int]:
        """Returns sum of XP earned across each category."""
        stmt = (
            select(XPTransaction.category, func.sum(XPTransaction.amount))
            .where(XPTransaction.user_id == user_id)
            .group_by(XPTransaction.category)
        )
        res = await self.db.execute(stmt)
        return {row[0]: int(row[1]) for row in res.all()}
