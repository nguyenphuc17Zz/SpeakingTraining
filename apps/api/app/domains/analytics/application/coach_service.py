import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.analytics.application.coach_context_builder import CoachContextBuilder
from app.domains.analytics.application.coach_intent_classifier import CoachIntent, CoachIntentClassifier
from app.domains.analytics.domain.metric_definitions import MetricKey
from app.domains.analytics.models import CoachConversation, CoachFeedback
from app.domains.analytics.prompts import (
    COACH_GENERAL_USER_PROMPT,
    COACH_SYSTEM_INSTRUCTION,
)
from app.domains.analytics.schemas import (
    CoachAnswerDTO,
    CoachQuickCardDTO,
    CoachRecommendationDTO,
    DailyBriefingDTO,
)
from app.domains.gamification.models import GameProfile


class CoachService:
    """
    Personal AI Speaking Coach orchestration engine.
    Blends instant deterministic fact-answering with grounded AI coaching and actionable recommendations.
    """

    def __init__(self, db: AsyncSession, ai_router: AIRouter | None = None):
        self.db = db
        self.ai_router = ai_router
        self.context_builder = CoachContextBuilder(db)

    async def answer(
        self, user_id: str, question: str, session_context_id: str | None = None
    ) -> CoachAnswerDTO:
        """
        Processes a learner query and produces a grounded, transparent coaching answer.
        """
        start_time = time.time()
        intent = CoachIntentClassifier.classify(question)
        context = await self.context_builder.build_context(user_id)

        # 1. Deterministic Fast Paths
        if intent == CoachIntent.SIMPLE_DATA:
            ans = await self._handle_simple_data(user_id, context, question)
            await self._persist_conversation(user_id, question, intent.value, ans, context.context_hash, int((time.time() - start_time) * 1000))
            return ans

        if intent == CoachIntent.WEAKNESS:
            ans = await self._handle_weakness_query(context, question)
            await self._persist_conversation(user_id, question, intent.value, ans, context.context_hash, int((time.time() - start_time) * 1000))
            return ans

        if intent == CoachIntent.RECOMMENDATION:
            ans = await self._handle_recommendation_query(context, question)
            await self._persist_conversation(user_id, question, intent.value, ans, context.context_hash, int((time.time() - start_time) * 1000))
            return ans

        # 2. AI-Powered Grounded Coaching (Diagnostic, Trend, General)
        if self.ai_router:
            try:
                ans = await self._generate_ai_coaching_answer(context, question, intent)
                latency = int((time.time() - start_time) * 1000)
                await self._persist_conversation(user_id, question, intent.value, ans, context.context_hash, latency)
                return ans
            except Exception as e:
                logger.warning(f"[CoachService] AI generation failed: {e}. Falling back to deterministic answer.")

        # Fallback deterministic answer
        ans = self._generate_fallback_answer(context, question, intent)
        await self._persist_conversation(user_id, question, intent.value, ans, context.context_hash, int((time.time() - start_time) * 1000))
        return ans

    async def _handle_simple_data(self, user_id: str, ctx: Any, question: str) -> CoachAnswerDTO:
        # Check streak from GameProfile
        prof_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        streak_val = profile.current_streak if profile else 0
        xp_val = profile.total_xp if profile else 0

        answer_text = (
            f"Theo dữ liệu luyện tập thực tế của bạn:\n\n"
            f"- **Tổng số buổi hội thoại đã phân tích:** {ctx.total_sessions} buổi\n"
            f"- **Chuỗi ngày luyện tập liên tục (Streak):** {streak_val} ngày 🔥\n"
            f"- **Tổng điểm kinh nghiệm tích luỹ:** {xp_val:,} XP\n\n"
            f"Bạn đang duy trì nhịp độ rất tốt. Hãy hoàn thành 1 bài tập hôm nay để giữ vững chuỗi luyện tập!"
        )

        return CoachAnswerDTO(
            answer=answer_text,
            intent_type=CoachIntent.SIMPLE_DATA.value,
            key_points=[f"Chuỗi {streak_val} ngày", f"{ctx.total_sessions} buổi đã phân tích"],
            evidence_refs=[{"source": "learner_profile", "sessions": ctx.total_sessions, "streak": streak_val}],
            recommendations=[
                CoachRecommendationDTO(
                    action_type="conversation",
                    target="daily_speaking_practice",
                    reason="Duy trì chuỗi luyện tập hôm nay",
                    duration_minutes=10,
                    practice_url="/speaking",
                )
            ],
            confidence="high",
            is_deterministic=True,
            context_hash=ctx.context_hash,
            generated_at=datetime.now(timezone.utc),
        )

    async def _handle_weakness_query(self, ctx: Any, question: str) -> CoachAnswerDTO:
        bottleneck = ctx.dashboard_overview.bottleneck
        ans_text = (
            f"Dựa trên các buổi luyện tập gần đây, điểm cần ưu tiên cải thiện nhất của bạn là:\n\n"
            f"🎯 **{bottleneck.candidate if bottleneck else 'Tốc độ phản xạ'}**\n\n"
            f"{bottleneck.description if bottleneck else 'Hãy tập trung vào các mẫu câu giao tiếp tự nhiên.'}\n\n"
            f"**Các điểm yếu cụ thể đã ghi nhận:**\n"
            f"{ctx.recent_weaknesses}"
        )

        return CoachAnswerDTO(
            answer=ans_text,
            intent_type=CoachIntent.WEAKNESS.value,
            key_points=[bottleneck.candidate if bottleneck else "Điểm nghẽn phản xạ"],
            evidence_refs=[{"bottleneck": bottleneck.candidate if bottleneck else "none"}],
            recommendations=[
                CoachRecommendationDTO(
                    action_type="drill",
                    target="weakness_priority_drill",
                    reason=f"Giải quyết điểm nghẽn: {bottleneck.candidate if bottleneck else 'Phản xạ'}",
                    duration_minutes=10,
                    practice_url="/learning",
                )
            ],
            confidence="high",
            is_deterministic=True,
            context_hash=ctx.context_hash,
            generated_at=datetime.now(timezone.utc),
        )

    async def _handle_recommendation_query(self, ctx: Any, question: str) -> CoachAnswerDTO:
        bottleneck = ctx.dashboard_overview.bottleneck
        focus = bottleneck.suggested_focus if bottleneck else "Hội thoại tự do 10 phút"

        ans_text = (
            f"Để tối ưu hiệu quả học hôm nay, tôi khuyên bạn nên tập trung vào:\n\n"
            f"👉 **{focus}**\n\n"
            f"**Lý do:** {bottleneck.description if bottleneck else 'Giúp duy trì phản xạ và phát âm chuẩn xác.'}\n\n"
            f"Chỉ cần dành ra 10–15 phút tập trung vào đúng bài tập này, hệ thống sẽ tự động đo lường độ tiến bộ ở lần phân tích tiếp theo."
        )

        return CoachAnswerDTO(
            answer=ans_text,
            intent_type=CoachIntent.RECOMMENDATION.value,
            key_points=[f"Trọng tâm hôm nay: {focus}"],
            evidence_refs=[],
            recommendations=[
                CoachRecommendationDTO(
                    action_type="conversation",
                    target="today_recommended_drill",
                    reason=f"Tập trung vào {focus}",
                    duration_minutes=10,
                    practice_url="/speaking",
                )
            ],
            confidence="high",
            is_deterministic=True,
            context_hash=ctx.context_hash,
            generated_at=datetime.now(timezone.utc),
        )

    async def _generate_ai_coaching_answer(
        self, ctx: Any, question: str, intent: CoachIntent
    ) -> CoachAnswerDTO:
        prompt = COACH_GENERAL_USER_PROMPT.format(
            speaking_level=ctx.speaking_level,
            level_confidence=ctx.level_confidence,
            total_sessions=ctx.total_sessions,
            active_goals=ctx.active_goals,
            period="30 ngày gần nhất",
            metrics_summary=ctx.metrics_summary,
            bottleneck_info=ctx.bottleneck_info,
            recent_weaknesses=ctx.recent_weaknesses,
            recent_strengths=ctx.recent_strengths,
            practice_distribution=ctx.practice_distribution,
            question=question,
        )

        req = AIRequest(
            task=AITask.COACH,
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
            system_instruction=COACH_SYSTEM_INSTRUCTION,
            temperature=0.3,
        )

        resp = await self.ai_router.generate(req)
        # Parse JSON
        parsed: dict[str, Any] = {}
        try:
            parsed = json.loads(resp.text)
        except Exception:
            # Fallback if raw text returned
            parsed = {
                "answer": resp.text,
                "key_points": ["Phân tích từ AI Coach"],
                "evidence_refs": [],
                "recommendations": [
                    {
                        "action_type": "conversation",
                        "target": "ai_recommended_practice",
                        "reason": "Luyện tập theo lời khuyên của Coach",
                        "duration_minutes": 10,
                    }
                ],
                "confidence": "medium",
            }

        recs: list[CoachRecommendationDTO] = []
        for r in parsed.get("recommendations", []):
            recs.append(
                CoachRecommendationDTO(
                    action_type=r.get("action_type", "conversation"),
                    target=r.get("target", "practice_session"),
                    reason=r.get("reason", "Luyện tập theo hướng dẫn"),
                    duration_minutes=r.get("duration_minutes", 10),
                    expected_signal=r.get("expected_signal"),
                    practice_url="/speaking" if r.get("action_type") == "conversation" else "/learning",
                )
            )

        return CoachAnswerDTO(
            answer=parsed.get("answer", resp.text),
            intent_type=intent.value,
            key_points=parsed.get("key_points", []),
            evidence_refs=parsed.get("evidence_refs", []),
            recommendations=recs,
            confidence=parsed.get("confidence", "medium"),
            is_deterministic=False,
            context_hash=ctx.context_hash,
            generated_at=datetime.now(timezone.utc),
        )

    def _generate_fallback_answer(
        self, ctx: Any, question: str, intent: CoachIntent
    ) -> CoachAnswerDTO:
        bottleneck = ctx.dashboard_overview.bottleneck
        ans_text = (
            f"Dựa trên {ctx.total_sessions} buổi luyện tập đã phân tích:\n\n"
            f"Trình độ hiện tại của bạn ước tính ở mức **{ctx.speaking_level}**.\n"
            f"Trọng tâm phát triển hiện tại: **{bottleneck.candidate if bottleneck else 'Tự nhiên hoá biểu đạt'}**.\n\n"
            f"Hãy tiếp tục duy trì 10–15 phút luyện nói mỗi ngày để hệ thống cập nhật thêm dữ liệu phân tích chi tiết."
        )

        return CoachAnswerDTO(
            answer=ans_text,
            intent_type=intent.value,
            key_points=["Phân tích tổng quan từ dữ liệu"],
            evidence_refs=[],
            recommendations=[
                CoachRecommendationDTO(
                    action_type="conversation",
                    target="regular_speaking",
                    reason="Duy trì thói quen luyện nói",
                    duration_minutes=10,
                    practice_url="/speaking",
                )
            ],
            confidence="medium",
            is_deterministic=True,
            context_hash=ctx.context_hash,
            generated_at=datetime.now(timezone.utc),
        )

    async def _persist_conversation(
        self,
        user_id: str,
        question: str,
        intent_type: str,
        answer_dto: CoachAnswerDTO,
        context_hash: str,
        latency_ms: int,
    ) -> None:
        rec = CoachConversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            question=question,
            intent_type=intent_type,
            answer_text=answer_dto.answer,
            key_points_json=answer_dto.key_points,
            evidence_refs_json=answer_dto.evidence_refs,
            recommendations_json=[r.model_dump() for r in answer_dto.recommendations],
            confidence=answer_dto.confidence,
            context_hash=context_hash,
            latency_ms=latency_ms,
        )
        self.db.add(rec)
        await self.db.commit()

    async def get_daily_briefing(self, user_id: str, persona: str = "tanaka") -> DailyBriefingDTO:
        """Constructs an AI-powered or deterministic daily briefing from Sensei."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ctx = await self.context_builder.build_context(user_id)
        bottleneck = ctx.dashboard_overview.bottleneck

        # 1. AI Generation if router is available
        if self.ai_router:
            try:
                from app.domains.coach.prompt_builder import PERSONA_INSTRUCTIONS
                persona_guide = PERSONA_INSTRUCTIONS.get(persona, PERSONA_INSTRUCTIONS["tanaka"])
                prompt = (
                    f"{persona_guide}\n\n"
                    f"Hãy soạn một bức thư ngắn đầu ngày (Daily Sensei Briefing) gửi cho học viên luyện nói tiếng Nhật:\n"
                    f"- Trình độ hiện tại: {ctx.speaking_level}\n"
                    f"- Tổng số buổi luyện: {ctx.total_sessions}\n"
                    f"- Điểm nghẽn cần khắc phục: {bottleneck.candidate if bottleneck else 'Phản xạ tự nhiên'}\n"
                    f"- Mô tả điểm nghẽn: {bottleneck.description if bottleneck else 'Cần tăng tốc độ và chuẩn hóa ngữ điệu'}\n\n"
                    f"Yêu cầu trả về đúng định dạng JSON:\n"
                    f"{{\n"
                    f"  \"yesterday_summary\": \"<1-2 câu tóm tắt tiến độ và khích lệ chân thành>\",\n"
                    f"  \"today_focus_title\": \"<Tiêu đề nhiệm vụ trọng tâm hôm nay>\",\n"
                    f"  \"today_focus_reason\": \"<Lý do và phương pháp ngắn gọn>\",\n"
                    f"  \"streak_status\": \"<Lời cổ vũ giữ chuỗi luyện tập>\"\n"
                    f"}}"
                )
                req = AIRequest(
                    messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
                    system_instruction="Bạn là AI Sensei tiếng Nhật. Trả về đúng định dạng JSON.",
                    temperature=0.7,
                )
                resp = await self.ai_router.generate(task=AITask.COACH_INSIGHT, request=req, user_id=user_id)
                t = resp.text.strip()
                if t.startswith("```"):
                    t = t.split("\n", 1)[-1] if "\n" in t else t
                    if t.endswith("```"):
                        t = t[:-3]
                    t = t.strip()
                    if t.startswith("json"):
                        t = t[4:].strip()
                parsed = json.loads(t)

                return DailyBriefingDTO(
                    date=today_str,
                    yesterday_summary=parsed.get("yesterday_summary", f"Bạn đang ở trình độ {ctx.speaking_level}."),
                    today_focus_title=parsed.get("today_focus_title", bottleneck.candidate if bottleneck else "Luyện tập phản xạ"),
                    today_focus_reason=parsed.get("today_focus_reason", bottleneck.description if bottleneck else "Tăng độ mượt mà"),
                    recommendation=CoachRecommendationDTO(
                        action_type="conversation",
                        target="daily_focus_session",
                        reason=bottleneck.suggested_focus if bottleneck else "10 phút luyện tập",
                        duration_minutes=10,
                        practice_url="/learning",
                    ),
                    streak_status=parsed.get("streak_status", "Cùng giữ vững chuỗi luyện tập hôm nay! 🔥"),
                )
            except Exception as e:
                logger.warning(f"[CoachService] AI daily briefing fallback: {e}")

        # 2. Fallback deterministic
        return DailyBriefingDTO(
            date=today_str,
            yesterday_summary=f"Bạn đang ở trình độ {ctx.speaking_level} với {ctx.total_sessions} buổi đã phân tích.",
            today_focus_title=bottleneck.candidate if bottleneck else "Luyện tập phản xạ hội thoại",
            today_focus_reason=bottleneck.description if bottleneck else "Tăng cường độ mượt mà khi nói.",
            recommendation=CoachRecommendationDTO(
                action_type="conversation",
                target="daily_focus_session",
                reason=bottleneck.suggested_focus if bottleneck else "10 phút hội thoại tình huống",
                duration_minutes=10,
                practice_url="/learning",
            ),
            streak_status="Tiếp tục chuỗi luyện tập hôm nay! 🔥",
        )

    async def get_quick_cards(self, user_id: str) -> list[CoachQuickCardDTO]:
        """Provides pre-computed data for top quick-access cards."""
        ctx = await self.context_builder.build_context(user_id)
        overview = ctx.dashboard_overview

        cards = [
            CoachQuickCardDTO(
                card_type="progress",
                title="Tiến độ học tập",
                summary=f"Trình độ {ctx.speaking_level} ({ctx.total_sessions} buổi đã phân tích)",
                action_cta="Xem chi tiết",
                action_url="/progress",
            ),
            CoachQuickCardDTO(
                card_type="weakness",
                title="Điểm cần cải thiện",
                summary=overview.bottleneck.candidate if overview.bottleneck else "Tự nhiên hoá biểu đạt",
                action_cta="Khắc phục ngay",
                action_url="/learning",
            ),
            CoachQuickCardDTO(
                card_type="what_to_practice",
                title="Gợi ý hôm nay",
                summary=overview.bottleneck.suggested_focus if overview.bottleneck else "10 phút hội thoại tự do",
                action_cta="Luyện tập",
                action_url="/speaking",
            ),
        ]
        return cards
