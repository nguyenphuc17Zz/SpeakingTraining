from datetime import datetime, timezone
from typing import Any
import json

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation_intelligence.models import SessionAnalysis, TurnAnalysis
from app.domains.learning.models import ExerciseAttempt
from app.domains.learner_memory.level_assessor import LevelAssessor
from app.domains.learner_memory.mastery import MasteryEstimator
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile, MemoryEvidence
from app.domains.learner_memory.scorer import MemoryScorer
from app.domains.learner_memory.trend_analyzer import TrendAnalyzer


class LearnerProfileService:
    """Orchestrates long-term learner profile recalculation, scoring updates, and AI learner summary synthesis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def get_or_create_profile(self, user_id: str) -> LearnerProfile:
        """Retrieves existing profile or creates a clean starting profile."""
        stmt = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        res = await self.db.execute(stmt)
        profile = res.scalar_one_or_none()

        if not profile:
            profile = LearnerProfile(
                user_id=user_id,
                overall_level="intermediate",
                speaking_level="intermediate",
                fluency_level="intermediate",
                grammar_level="intermediate",
                vocabulary_level="intermediate",
                naturalness_level="intermediate",
                confidence_score=0.35,
                level_confidence="insufficient_evidence",
                total_sessions_analyzed=0,
                total_turns_analyzed=0,
                strengths=[],
                weaknesses=[],
                learning_goals=["Giao tiếp tự nhiên trong hội thoại đời sống và công việc"],
                summary="Người học đang bắt đầu lộ trình luyện nói tiếng Nhật phản xạ.",
                summary_version=1,
                last_recalculated_at=datetime.now(timezone.utc),
            )
            self.db.add(profile)
            await self.db.flush()

        return profile

    async def recalculate_profile(
        self,
        user_id: str,
        generate_ai_summary: bool = True,
    ) -> LearnerProfile:
        """Fully recalculates all user memories, scoring, mastery, trends, levels, and profile synthesis."""
        profile = await self.get_or_create_profile(user_id)

        # 1. Fetch all user sessions and attempts across ALL 4 Studio modes
        sessions_stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id,
            ConversationSession.status == "completed",
        )
        s_res = await self.db.execute(sessions_stmt)
        sessions = s_res.scalars().all()
        session_ids = [s.id for s in sessions]

        # Fetch all studio exercise attempts
        attempts_stmt = (
            select(ExerciseAttempt)
            .options(selectinload(ExerciseAttempt.exercise))
            .where(
                ExerciseAttempt.user_id == user_id,
                ExerciseAttempt.status == "completed",
            )
        )
        att_res = await self.db.execute(attempts_stmt)
        attempts = list(att_res.scalars().all())

        # Fetch pronunciation attempts
        from app.domains.pronunciation.models import PronunciationAttempt
        pron_stmt = select(PronunciationAttempt).where(
            PronunciationAttempt.user_id == user_id,
            PronunciationAttempt.analysis_status == "completed",
        )
        pron_res = await self.db.execute(pron_stmt)
        pron_attempts = list(pron_res.scalars().all())

        total_sessions = len(sessions) + len(attempts)
        total_turns = len(sessions) * 6 + len(attempts)

        # 2. Compute 4 core skill scores (0 - 100)
        latencies = []
        for a in attempts:
            rm = (a.metrics_json or {}).get("reflex", {}) if a.metrics_json else {}
            lat = rm.get("reaction_latency_ms", a.response_speed_ms)
            if lat is not None and lat > 0:
                latencies.append(float(lat))
        avg_latency = float(sum(latencies) / len(latencies)) if latencies else 1850.0

        fluency_score = max(30.0, min(95.0, round(100.0 - (avg_latency / 3000.0 * 50.0), 1)))

        correct_count = sum(1 for a in attempts if a.success)
        grammar_score = (
            round(correct_count / len(attempts) * 100.0, 1)
            if attempts
            else 75.0
        )

        pron_scores = [p.overall_score for p in pron_attempts if p.overall_score is not None]
        pron_score = round(sum(pron_scores) / len(pron_scores), 1) if pron_scores else 78.0

        vocab_score = max(50.0, min(95.0, round((grammar_score * 0.5) + (fluency_score * 0.5), 1)))
        composite_score = round((fluency_score + grammar_score + pron_score + vocab_score) / 4.0, 1)

        # 3. Determine JLPT & CEFR Level
        if composite_score >= 88.0:
            jlpt_level = "N1"
            cefr_level = "C1"
            overall_level_label = "advanced"
        elif composite_score >= 78.0:
            jlpt_level = "N2"
            cefr_level = "B2"
            overall_level_label = "upper_intermediate"
        elif composite_score >= 65.0:
            jlpt_level = "N3"
            cefr_level = "B1"
            overall_level_label = "intermediate"
        elif composite_score >= 50.0:
            jlpt_level = "N4"
            cefr_level = "A2"
            overall_level_label = "elementary"
        else:
            jlpt_level = "N5"
            cefr_level = "A1"
            overall_level_label = "beginner"

        # 4. Fetch and recalculate all user memories
        memories_stmt = (
            select(LearnerMemory)
            .where(LearnerMemory.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        m_res = await self.db.execute(memories_stmt)
        memories = m_res.scalars().all()

        for mem in memories:
            ev_stmt = (
                select(MemoryEvidence)
                .where(MemoryEvidence.memory_id == mem.id)
                .order_by(MemoryEvidence.created_at)
            )
            ev_res = await self.db.execute(ev_stmt)
            evidences = ev_res.scalars().all()

            unique_sessions = len({e.session_id for e in evidences})
            mem.evidence_count = len(evidences)
            mem.contexts_used = list({e.context_tag for e in evidences if e.context_tag})
            mem.confidence = MemoryScorer.calculate_confidence(
                evidence_count=len(evidences),
                unique_sessions_count=unique_sessions,
            )
            mem.mastery = MasteryEstimator.estimate_mastery(mem)
            trend, status = TrendAnalyzer.analyze_trend(mem, evidences)
            mem.trend = trend.value
            if mem.status not in ("dismissed", "archived"):
                mem.status = status

            if mem.memory_type == "strength":
                mem.priority_score = MemoryScorer.calculate_strength_score(
                    mem, unique_sessions, max(1, total_sessions)
                )
            else:
                mem.priority_score = MemoryScorer.calculate_weakness_priority(
                    mem, unique_sessions, max(1, total_sessions)
                )

        await self.db.flush()

        weaknesses_pool = [
            m for m in memories
            if m.memory_type in ("grammar", "particle", "conjugation", "politeness", "filler", "word_choice", "vocabulary", "naturalness")
            and m.status not in ("dismissed", "archived")
        ]
        weaknesses_pool.sort(key=lambda m: (m.priority_score, m.last_seen), reverse=True)

        top_weaknesses_data = []
        for w in weaknesses_pool[:5]:
            top_weaknesses_data.append({
                "id": w.id,
                "key": w.key,
                "statement": w.statement,
                "category": w.category or w.memory_type,
                "priority_score": round(w.priority_score, 2),
                "mastery": round(w.mastery, 2),
                "trend": w.trend,
                "evidence_count": w.evidence_count,
                "is_regression": w.is_regression,
                "severity": w.severity,
                "last_seen": w.last_seen.isoformat() if w.last_seen else None,
            })

        strengths_pool = [
            m for m in memories
            if m.memory_type == "strength" and m.status not in ("dismissed", "archived")
        ]
        strengths_pool.sort(key=lambda m: (m.priority_score, m.last_seen), reverse=True)

        top_strengths_data = []
        for s in strengths_pool[:5]:
            top_strengths_data.append({
                "id": s.id,
                "key": s.key,
                "statement": s.statement,
                "priority_score": round(s.priority_score, 2),
                "mastery": round(s.mastery, 2),
                "evidence_count": s.evidence_count,
                "last_seen": s.last_seen.isoformat() if s.last_seen else None,
            })

        goals_pool = [m.statement for m in memories if m.memory_type == "goal" and m.status != "dismissed"]
        learning_goals = goals_pool if goals_pool else (profile.learning_goals or ["Giao tiếp tự nhiên trong đời sống và công việc"])

        profile.overall_level = overall_level_label
        profile.speaking_level = overall_level_label
        profile.fluency_level = "upper_intermediate" if fluency_score >= 75 else "intermediate"
        profile.grammar_level = "upper_intermediate" if grammar_score >= 75 else "intermediate"
        profile.vocabulary_level = "upper_intermediate" if vocab_score >= 75 else "intermediate"
        profile.naturalness_level = "upper_intermediate" if pron_score >= 75 else "intermediate"
        profile.confidence_score = 0.85 if total_sessions >= 10 else 0.55
        profile.level_confidence = "high" if total_sessions >= 10 else "medium"
        profile.total_sessions_analyzed = total_sessions
        profile.total_turns_analyzed = total_turns
        profile.avg_response_speed_ms = avg_latency
        profile.weaknesses = top_weaknesses_data
        profile.strengths = top_strengths_data
        profile.learning_goals = learning_goals

        if top_weaknesses_data:
            profile.current_focus = f"Khắc phục {top_weaknesses_data[0]['statement']}"
        else:
            profile.current_focus = "Nâng cao phản xạ hội thoại và chuẩn hóa Kính ngữ công sở"

        # 5. Synthesize AI Learner Summary
        if generate_ai_summary and total_sessions >= 1:
            try:
                prompt = (
                    f"Hãy soạn một bản nhận xét năng lực hội thoại tổng quan (Speaking Portfolio Certificate Summary) cho học viên:\n"
                    f"- Tổng số lượt luyện tập: {total_sessions} buổi\n"
                    f"- Điểm Trôi chảy: {fluency_score}% (Độ trễ trung bình: {int(avg_latency)}ms)\n"
                    f"- Điểm Ngữ pháp: {grammar_score}%\n"
                    f"- Điểm Ngữ âm: {pron_score}%\n"
                    f"- Ước tính cấp độ: {jlpt_level} ({cefr_level})\n"
                    f"- Điểm mạnh: {', '.join([s['statement'] for s in top_strengths_data]) if top_strengths_data else 'Phản xạ câu đơn tốt'}\n"
                    f"- Cần cải thiện: {', '.join([w['statement'] for w in top_weaknesses_data]) if top_weaknesses_data else 'Kính ngữ và ngữ điệu'}\n\n"
                    f"Yêu cầu: Viết 2-3 câu nhận xét truyền cảm hứng, chuẩn phong cách Nhật Bản, ghi nhận nỗ lực rèn luyện của học viên."
                )
                req = AIRequest(
                    messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
                    system_instruction="Bạn là AI Sensei cố vấn ngôn ngữ tiếng Nhật. Viết nhận xét ngắn gọn, ấm áp, sâu sắc.",
                    temperature=0.7,
                )
                resp = await self.ai_router.generate(task=AITask.COACH_INSIGHT, request=req, user_id=user_id)
                profile.summary = resp.text.strip()
                profile.summary_version += 1
                profile.summary_generated_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.warning(f"[LearnerProfileService] AI summary fallback: {e}")
                profile.summary = f"Học viên đã hoàn thành {total_sessions} buổi luyện với tốc độ phản xạ {int(avg_latency)}ms. Năng lực hội thoại ước tính đạt chuẩn {jlpt_level} ({cefr_level})."

        profile.last_recalculated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info(f"[LearnerProfileService] Recalculated profile for user '{user_id}' (JLPT: {jlpt_level})")
        return profile
