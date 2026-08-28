from datetime import date, datetime, timedelta, timezone
from typing import Any
import zoneinfo
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import GameEventType, XPCategory
from app.domains.gamification.models import DailyStreakActivity, GameProfile
from app.domains.settings.models import UserSettings
from app.domains.users.models import User


class StreakService:
    """
    Timezone-aware learning streak calculation engine.
    Streaks require meaningful learning activity (speaking, exercise, pronunciation, shadowing),
    NOT just opening the app or logging in.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_timezone(self, user_id: str) -> str:
        """Retrieves configured user timezone with fallback to 'Asia/Tokyo'."""
        stmt = select(UserSettings.timezone).where(UserSettings.user_id == user_id)
        res = await self.db.execute(stmt)
        tz = res.scalar_one_or_none()
        if tz:
            return tz
        u_stmt = select(User.timezone).where(User.id == user_id)
        u_res = await self.db.execute(u_stmt)
        return u_res.scalar_one_or_none() or "Asia/Tokyo"

    def _resolve_tz(self, tz_name: str) -> timezone | zoneinfo.ZoneInfo:
        try:
            return zoneinfo.ZoneInfo(tz_name)
        except Exception:
            try:
                return zoneinfo.ZoneInfo("Asia/Tokyo")
            except Exception:
                return timezone(timedelta(hours=9))

    def get_current_date_in_tz(self, tz_name: str) -> str:
        """Returns today's date in 'YYYY-MM-DD' formatted according to user timezone."""
        tz = self._resolve_tz(tz_name)
        return datetime.now(tz).strftime("%Y-%m-%d")

    async def record_qualifying_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_id: str,
    ) -> tuple[int, bool]:
        """
        Records a meaningful learning activity for today's streak.
        Updates GameProfile streak if today newly qualifies.
        Returns: (new_current_streak, is_newly_incremented)
        """
        tz_name = await self.get_user_timezone(user_id)
        today_str = self.get_current_date_in_tz(tz_name)

        # 1. Insert streak activity record (idempotent)
        chk_stmt = select(DailyStreakActivity).where(
            DailyStreakActivity.user_id == user_id,
            DailyStreakActivity.activity_date == today_str,
            DailyStreakActivity.activity_type == activity_type,
            DailyStreakActivity.activity_id == activity_id,
        )
        chk_res = await self.db.execute(chk_stmt)
        if not chk_res.scalar_one_or_none():
            activity_rec = DailyStreakActivity(
                user_id=user_id,
                activity_date=today_str,
                activity_type=activity_type,
                activity_id=activity_id,
            )
            self.db.add(activity_rec)
            await self.db.commit()

        # 2. Update Profile Streak
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        if not profile:
            from app.domains.gamification.domain.level_curve import LevelCurve
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

        last_date_str = profile.last_active_date

        if last_date_str == today_str:
            # Already active today, streak intact
            return profile.current_streak, False

        # Calculate difference from last active date
        is_new_increment = False
        if not last_date_str:
            profile.current_streak = 1
            profile.longest_streak = max(profile.longest_streak, 1)
            is_new_increment = True
        else:
            try:
                last_dt = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                today_dt = datetime.strptime(today_str, "%Y-%m-%d").date()
                delta_days = (today_dt - last_dt).days

                if delta_days == 1:
                    # Consecutive day!
                    profile.current_streak += 1
                    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
                    is_new_increment = True
                elif delta_days == 2 and profile.streak_freezes_available > 0:
                    # Used a streak freeze to save the streak
                    profile.streak_freezes_available -= 1
                    profile.current_streak += 1
                    profile.longest_streak = max(profile.longest_streak, profile.current_streak)
                    is_new_increment = True
                    logger.info(f"[StreakService] User {user_id} used a streak freeze to protect streak!")
                else:
                    # Streak broken, reset to 1
                    profile.current_streak = 1
                    is_new_increment = True
            except Exception as e:
                logger.warning(f"[StreakService] Error calculating streak delta: {e}")
                profile.current_streak = 1
                is_new_increment = True

        profile.last_active_date = today_str
        await self.db.commit()
        await self.db.refresh(profile)

        return profile.current_streak, is_new_increment

    async def get_streak_overview(self, user_id: str) -> dict[str, Any]:
        """Returns comprehensive streak telemetry for dashboard and profile views."""
        tz_name = await self.get_user_timezone(user_id)
        today_str = self.get_current_date_in_tz(tz_name)

        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        current_streak = profile.current_streak if profile else 0
        longest_streak = profile.longest_streak if profile else 0
        freezes = profile.streak_freezes_available if profile else 0
        last_date = profile.last_active_date if profile else None

        # Check today's qualifying activities
        act_stmt = (
            select(func.count(DailyStreakActivity.id))
            .where(
                DailyStreakActivity.user_id == user_id,
                DailyStreakActivity.activity_date == today_str,
            )
        )
        act_res = await self.db.execute(act_stmt)
        today_count = act_res.scalar() or 0

        # Activity in the last 7 days
        today_dt = datetime.strptime(today_str, "%Y-%m-%d").date()
        history_list = []
        for i in range(6, -1, -1):
            day_dt = today_dt - timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            d_stmt = (
                select(func.count(DailyStreakActivity.id))
                .where(
                    DailyStreakActivity.user_id == user_id,
                    DailyStreakActivity.activity_date == day_str,
                )
            )
            d_res = await self.db.execute(d_stmt)
            count = d_res.scalar() or 0
            history_list.append({
                "date": day_str,
                "day_name": day_dt.strftime("%a"),
                "is_active": count > 0,
                "activity_count": count,
            })

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "streak_freezes_available": freezes,
            "is_qualified_today": today_count > 0 or last_date == today_str,
            "today_activities_count": today_count,
            "qualifying_threshold_met": today_count > 0,
            "last_active_date": last_date,
            "activity_history_last_7_days": history_list,
        }
