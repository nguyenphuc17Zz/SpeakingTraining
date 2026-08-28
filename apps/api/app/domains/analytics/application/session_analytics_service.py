from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.analytics.models import SessionAnalyticsRecord
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation_intelligence.models import TurnAnalysis


class SessionAnalyticsService:
    """Computes session-level analytics and persists SessionAnalyticsRecord."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_session_analytics(self, session_id: str) -> SessionAnalyticsRecord | None:
        """
        Derives summary analytics for a completed session.
        Idempotent: updates existing record if already generated.
        """
        sess_stmt = select(ConversationSession).where(ConversationSession.id == session_id)
        sess_res = await self.db.execute(sess_stmt)
        session = sess_res.scalar_one_or_none()
        if not session:
            return None

        # Fetch turns
        turns_stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.session_id == session_id)
            .order_by(ConversationTurn.sequence.asc())
        )
        turns_res = await self.db.execute(turns_stmt)
        turns = list(turns_res.scalars().all())

        user_turns = [t for t in turns if t.speaker == "user"]
        assistant_turns = [t for t in turns if t.speaker == "assistant"]

        # Fetch turn analyses
        turn_ids = [t.id for t in turns]
        analyses: list[TurnAnalysis] = []
        if turn_ids:
            ana_stmt = select(TurnAnalysis).where(TurnAnalysis.turn_id.in_(turn_ids))
            ana_res = await self.db.execute(ana_stmt)
            analyses = list(ana_res.scalars().all())

        # Error counts
        grammar_errors = sum(
            1 for a in analyses for c in a.corrections if c.category in ("grammar", "particle", "conjugation")
        )
        naturalness_issues = sum(
            1 for a in analyses for c in a.corrections if c.category in ("naturalness", "word_choice", "politeness")
        )
        quality_avg = (
            sum(a.overall_quality_score for a in analyses) / len(analyses) if analyses else 80.0
        )

        # Average response latency
        speeds = [t.processing_time_ms for t in user_turns if t.processing_time_ms is not None]
        avg_speed = sum(speeds) / len(speeds) if speeds else None

        # Fillers
        dur_mins = max(0.5, (session.duration_seconds or 60) / 60.0)
        filler_count = sum(
            t.transcript.count("あの") + t.transcript.count("えーと") + t.transcript.count("なんか")
            for t in user_turns
        )
        filler_rate = round(filler_count / dur_mins, 1)

        # Upsert record
        rec_stmt = select(SessionAnalyticsRecord).where(SessionAnalyticsRecord.session_id == session_id)
        rec_res = await self.db.execute(rec_stmt)
        record = rec_res.scalar_one_or_none()

        if not record:
            record = SessionAnalyticsRecord(
                session_id=session_id,
                user_id=session.user_id,
                duration_seconds=session.duration_seconds or 0,
                speaking_time_seconds=int(session.duration_seconds or 0 * 0.4),  # estimate active speech
                user_turns_count=len(user_turns),
                assistant_turns_count=len(assistant_turns),
                grammar_error_count=grammar_errors,
                naturalness_issue_count=naturalness_issues,
                avg_response_speed_ms=avg_speed,
                filler_rate_per_min=filler_rate,
                quality_score=round(quality_avg, 1),
            )
            self.db.add(record)
        else:
            record.duration_seconds = session.duration_seconds or 0
            record.user_turns_count = len(user_turns)
            record.assistant_turns_count = len(assistant_turns)
            record.grammar_error_count = grammar_errors
            record.naturalness_issue_count = naturalness_issues
            record.avg_response_speed_ms = avg_speed
            record.filler_rate_per_min = filler_rate
            record.quality_score = round(quality_avg, 1)

        await self.db.commit()
        await self.db.refresh(record)
        logger.info(f"[SessionAnalyticsService] Computed analytics for session {session_id}")
        return record
