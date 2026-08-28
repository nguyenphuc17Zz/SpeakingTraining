from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learner_memory.contracts import LearnerContextBudget
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile


class MemoryRetriever:
    """Context-aware memory retrieval with strict token budgets for real-time conversation AI."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve_context(
        self,
        user_id: str,
        persona_role: str | None = None,
        topic_hint: str | None = None,
        max_items: int = 5,
    ) -> LearnerContextBudget:
        """Retrieves prioritized, context-matched learner memory facts formatted for LLM system context."""
        # 1. Fetch Profile
        prof_stmt = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        overall_lvl = profile.overall_level if profile else "intermediate"
        lvl_conf = profile.level_confidence if profile else "insufficient_evidence"
        goals = profile.learning_goals if profile and profile.learning_goals else ["Giao tiếp tự nhiên đời sống"]

        # 2. Fetch Active Memories (bounded pool to prevent unbounded table scans)
        fetch_limit = max(20, max_items * 4)
        mem_stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.status.in_(["active", "new", "improving"]),
            )
            .order_by(desc(LearnerMemory.priority_score))
            .limit(fetch_limit)
        )
        mem_res = await self.db.execute(mem_stmt)
        all_memories = mem_res.scalars().all()

        role_lower = (persona_role or "").lower()
        topic_lower = (topic_hint or "").lower()

        # 3. Score Relevance
        scored_items: list[tuple[float, LearnerMemory]] = []
        for mem in all_memories:
            rel_score = mem.priority_score

            # Relevance boosts based on situational role
            if ("boss" in role_lower or "interview" in role_lower or "senpai" in role_lower or "work" in role_lower) and "politeness" in mem.key:
                rel_score += 0.35
            elif ("casual" in role_lower or "friend" in role_lower) and "filler" in mem.key:
                rel_score += 0.20

            # Topic keyword match
            if topic_lower and mem.contexts_used and any(topic_lower in ctx.lower() for ctx in mem.contexts_used):
                rel_score += 0.25

            scored_items.append((rel_score, mem))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        selected_memories = [item[1] for item in scored_items[:max_items]]

        # Separate weaknesses vs strengths
        weaknesses_list: list[str] = []
        strengths_list: list[str] = []

        for m in selected_memories:
            if m.memory_type == "strength":
                strengths_list.append(f"{m.statement}")
            else:
                trend_symbol = "↗ Đang tiến bộ" if m.trend == "improving" else ("→ Duy trì" if m.trend == "stable" else "⚠️ Cần chú ý")
                if m.is_regression:
                    trend_symbol = "🔄 Tái phát"
                weaknesses_list.append(f"{m.statement} [{trend_symbol}]")

        # 4. Build Compact Prompt Block
        prompt_lines = [
            "<learner_memory>",
            f"[Hồ sơ người học: Trình độ {overall_lvl.upper()} (Độ tin cậy: {lvl_conf})]",
        ]

        if goals:
            prompt_lines.append(f"Mục tiêu giao tiếp: {goals[0]}")

        if weaknesses_list:
            prompt_lines.append("Lỗi thường gặp (Hãy tự nhiên tạo ngữ cảnh để người học luyện tập, không giảng giải máy móc):")
            for w in weaknesses_list[:4]:
                prompt_lines.append(f"  - {w}")

        if strengths_list:
            prompt_lines.append("Điểm mạnh đã xác nhận:")
            for s in strengths_list[:2]:
                prompt_lines.append(f"  - {s}")

        prompt_lines.append("</learner_memory>")

        compact_prompt = "\n".join(prompt_lines)

        return LearnerContextBudget(
            level=overall_lvl,
            level_confidence=lvl_conf,
            current_goals=goals,
            priority_weaknesses=weaknesses_list,
            speaking_strengths=strengths_list,
            current_focus=profile.current_focus if profile else None,
            compact_prompt_block=compact_prompt,
        )
