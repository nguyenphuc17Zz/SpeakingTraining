from typing import Sequence
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.domain.comparison_context import ComparisonContext
from app.domains.conversation.models import ConversationSession


class ComparisonEngine:
    """Groups, filters, and validates comparability of speaking sessions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_comparable_sessions(
        self,
        user_id: str,
        target_context: ComparisonContext,
        limit: int = 30,
        strict: bool = False,
    ) -> list[ConversationSession]:
        """
        Retrieves user sessions that match the target ComparisonContext.
        """
        stmt = (
            select(ConversationSession)
            .where(
                ConversationSession.user_id == user_id,
                ConversationSession.status == "completed",
            )
            .order_by(desc(ConversationSession.started_at))
            .limit(limit * 2)  # fetch buffer
        )
        res = await self.db.execute(stmt)
        sessions = list(res.scalars().all())

        matched: list[ConversationSession] = []
        for s in sessions:
            s_ctx = ComparisonContext.from_session_metadata(
                mode=s.mode,
                difficulty="normal",  # can be enriched from session extra metadata
                duration_seconds=s.duration_seconds,
                session_type="conversation",
            )
            if s_ctx.is_comparable_to(target_context, strict=strict):
                matched.append(s)
                if len(matched) >= limit:
                    break

        return matched
