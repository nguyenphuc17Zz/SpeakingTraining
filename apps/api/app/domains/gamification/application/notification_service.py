from datetime import datetime, timezone
from typing import Any
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.domain.contracts import NotificationPriority
from app.domains.gamification.models import RewardNotification
from app.domains.gamification.schemas import RewardNotificationDTO


class GamificationNotificationService:
    """
    Manages non-disruptive, prioritized reward notification queue.
    Notifications do not interrupt active speech/conversation turns.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: NotificationPriority | str = NotificationPriority.NORMAL,
        xp_amount: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> RewardNotification:
        """Enqueues a persistent reward notification."""
        pri_str = priority.value if isinstance(priority, NotificationPriority) else str(priority)

        notif = RewardNotification(
            user_id=user_id,
            notification_type=notification_type,
            priority=pri_str,
            title=title,
            message=message,
            xp_amount=xp_amount,
            payload_json=payload,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)

        logger.info(f"[NotificationService] Enqueued [{pri_str}] notification '{title}' for user {user_id}")
        return notif

    async def get_unread_notifications(self, user_id: str, limit: int = 20) -> list[RewardNotificationDTO]:
        """Fetches pending unread notifications ordered by priority and time."""
        stmt = (
            select(RewardNotification)
            .where(RewardNotification.user_id == user_id, RewardNotification.is_read == False)
            .order_by(desc(RewardNotification.created_at))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        items = list(res.scalars().all())

        return [
            RewardNotificationDTO(
                id=n.id,
                notification_type=n.notification_type,
                priority=n.priority,
                title=n.title,
                message=n.message,
                xp_amount=n.xp_amount,
                payload=n.payload_json or {},
                is_read=n.is_read,
                created_at=n.created_at,
            )
            for n in items
        ]

    async def mark_as_read(self, user_id: str, notification_id: str) -> None:
        """Marks a notification as seen/read."""
        stmt = select(RewardNotification).where(
            RewardNotification.id == notification_id,
            RewardNotification.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        notif = res.scalar_one_or_none()
        if notif:
            notif.is_read = True
            await self.db.commit()
