from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learner_memory.contracts import LearningPriority, MemoryTrend, MemoryType
from app.domains.learner_memory.models import LearnerMemory


class LearningPriorityService:
    """Computes and exposes prioritized learning weaknesses for adaptive recommendations and curriculum (Phase 7 contract)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_top_learning_priorities(
        self,
        user_id: str,
        limit: int = 5,
    ) -> list[LearningPriority]:
        """Returns top prioritized learning items ranked by urgency, recurrence, and mastery gap."""
        stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.memory_type.in_([
                    "grammar", "particle", "conjugation", "politeness", "filler", "word_choice", "vocabulary", "naturalness"
                ]),
                LearnerMemory.status.in_(["active", "new", "improving"]),
            )
            .order_by(desc(LearnerMemory.priority_score), desc(LearnerMemory.last_seen))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        memories = res.scalars().all()

        priorities: list[LearningPriority] = []
        for mem in memories:
            # Generate actionable pedagogical recommendation
            rec_focus = f"Luyện tập nhận diện và phản xạ đặt câu chuẩn với {mem.statement} trong các ngữ cảnh giao tiếp."
            if "particle" in mem.key:
                rec_focus = f"Tập trung phân biệt rõ vai trò chủ ngữ/tân ngữ khi dùng {mem.statement}."
            elif "keigo" in mem.key:
                rec_focus = "Luyện tập chuyển đổi thể lịch sự (です/ます) sang kính ngữ công sở."
            elif "filler" in mem.key:
                rec_focus = "Ý thức thay thế từ đệm ngập ngừng bằng khoảng lặng tự nhiên hoặc mẫu câu nối."

            reason_msg = f"Xuất hiện {mem.evidence_count} lần qua các buổi học (Độ thuần thục: {int(mem.mastery * 100)}%)"
            if mem.is_regression:
                reason_msg += " — Lỗi có dấu hiệu tái phát"

            try:
                m_type = MemoryType(mem.memory_type)
            except ValueError:
                m_type = MemoryType.GRAMMAR

            try:
                trend_val = MemoryTrend(mem.trend)
            except ValueError:
                trend_val = MemoryTrend.UNKNOWN

            priorities.append(
                LearningPriority(
                    key=mem.key,
                    type=m_type,
                    priority_score=mem.priority_score,
                    reason=reason_msg,
                    mastery=mem.mastery,
                    trend=trend_val,
                    recommended_focus=rec_focus,
                    evidence_count=mem.evidence_count,
                    last_seen=mem.last_seen,
                )
            )

        return priorities
