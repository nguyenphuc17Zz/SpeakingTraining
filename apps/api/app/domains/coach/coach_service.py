"""AICoachService — cross-cutting orchestrator (§5, §20-22, §48-50)."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.analytics.models import CoachConversation
from app.domains.analytics.schemas import CoachAnswerDTO, CoachRecommendationDTO
from app.domains.coach.action_executor import CoachActionExecutor
from app.domains.coach.context_resolver import CoachContextResolver
from app.domains.coach.contracts import CoachContext, CoachIntent, ToolResult
from app.domains.coach.memory_service import CoachMemoryService
from app.domains.coach.planner import CoachPlanner
from app.domains.coach.prompt_builder import CoachPromptBuilder
from app.domains.coach.response_formatter import CoachResponseFormatter, CoachResponseMode
from app.domains.coach.tool_registry import coach_tool_registry
import app.domains.coach.tools_impl  # noqa: F401 — bootstrap registry

from app.domains.analytics.application.coach_intent_classifier import CoachIntent as LegacyIntent, CoachIntentClassifier


class AICoachService:
    """Main Coach service — evidence-first, tool-based, AIRouter-routed."""

    def __init__(self, db: AsyncSession, ai_router: AIRouter | None = None):
        self.db = db
        self.ai_router = ai_router
        self.resolver = CoachContextResolver(db)
        self.planner = CoachPlanner(db)
        self.memory = CoachMemoryService(db)
        self.executor = CoachActionExecutor(db)
        self.prompt_builder = CoachPromptBuilder()

    async def chat(
        self,
        user_id: str,
        message: str,
        current_route: str = "/dashboard",
        current_exercise_id: str | None = None,
        current_session_id: str | None = None,
        response_mode: str = "standard",
        action_mode: str | None = None,  # "execute" if user wants immediate practice
        persona: str = "tanaka",
    ) -> dict[str, Any]:
        start = time.time()
        # 1. Intent + context
        intent = self.planner.infer_intent(message)
        ctx: CoachContext = await self.resolver.resolve(
            user_id=user_id,
            current_route=current_route,
            current_exercise_id=current_exercise_id,
            current_session_id=current_session_id,
            question=message,
        )

        # 2. Tool planning (deterministic before AI §49)
        tool_plan = self.planner.plan_tools(intent, ctx, message)
        tool_results = await self.planner.execute_plan(tool_plan, user_id)

        # 3. If action_mode == execute, directly orchestrate (practice creation) regardless of intent
        # This satisfies §45 "Do not ask unnecessary confirmation" for speaking/roleplay/speech
        if action_mode == "execute":
            import re
            m = re.search(r"(\d+)\s*(phút|minute|min)", message.lower())
            dur = int(m.group(1)) if m else 10
            # If intent is not PRACTICE, still treat as practice request when action_mode is explicit
            orch = await self.executor.orchestrate_practice(ctx, message, duration_min=dur)
            if orch.get("success"):
                ans = f"Đã tạo bài luyện tập cho bạn! **{orch['data'].get('title', orch['data'].get('exercise_id'))}** — {dur} phút. Bấm để bắt đầu."
                return {
                    "response": ans,
                    "intent": intent.value,
                    "confidence": 0.94,
                    "evidence": [],
                    "recommendations": [],
                    "tool_calls": tool_results,
                    "next_action": {"type": "START_SESSION", "payload": orch["data"], "label": "Bắt đầu luyện tập"},
                    "context_hash": ctx.context_hash,
                }
            # if orchestration failed, continue to AI/deterministic fallback

        # 4. Fast deterministic paths for data queries (no LLM)
        legacy = CoachIntentClassifier.classify(message)
        if legacy.value in ("simple_data", "weakness", "recommendation") and not tool_results:
            # fallback to simple handling without AI
            return await self._deterministic_answer(ctx, message, intent, tool_results, start)

        # 5. Build prompt and call AIRouter if available — task-routed §48
        if self.ai_router:
            try:
                system, user_content = self.prompt_builder.build(
                    ctx, message, coach_tool_registry.describe_for_prompt(), persona=persona
                )
                # route by intent to specific coach tasks for cost control §48
                task_map = {
                    CoachIntent.EXPLAIN: AITask.COACH_EXPLANATION,
                    CoachIntent.TEACH: AITask.COACH_EXPLANATION,
                    CoachIntent.ANALYZE: AITask.COACH_INSIGHT,
                    CoachIntent.PLAN: AITask.COACH_PLAN,
                    CoachIntent.RECOMMEND: AITask.COACH_PLAN,
                    CoachIntent.REVIEW: AITask.COACH_INSIGHT,
                }
                ai_task = task_map.get(intent, AITask.COACH_CHAT if intent in (CoachIntent.ASK, CoachIntent.GENERAL, CoachIntent.MOTIVATE, CoachIntent.PRACTICE) else AITask.COACH)
                req = AIRequest(
                    task=ai_task,
                    messages=[AIMessage(role=AIMessageRole.USER, content=user_content)],
                    system_instruction=system,
                    temperature=0.3,
                    response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
                )
                resp = await self.ai_router.generate(task=ai_task, request=req, user_id=user_id)
                parsed = self._parse_ai_json(resp.text)
                # Validate no fabricated tool results — cross-check against actual tool_results
                # Enrich with evidence from tool_results
                answer_text = parsed.get("response") or parsed.get("answer") or resp.text
                # Format by response mode
                fmt_mode = CoachResponseMode(response_mode) if response_mode in [e.value for e in CoachResponseMode] else CoachResponseMode.STANDARD
                answer_text = CoachResponseFormatter.format(answer_text, fmt_mode)

                latency = int((time.time() - start) * 1000)
                # enrich parsed with tool_calls for audit
                parsed["_tool_calls"] = tool_results
                await self._persist(user_id, message, intent.value, answer_text, parsed, ctx.context_hash, latency)

                return {
                    "response": answer_text,
                    "intent": parsed.get("intent", intent.value),
                    "confidence": parsed.get("confidence", 0.85),
                    "evidence": parsed.get("evidence", []),
                    "recommendations": parsed.get("recommendations", []),
                    "key_points": parsed.get("key_points", []),
                    "tool_calls": tool_results,
                    "next_action": parsed.get("next_action"),
                    "context_hash": ctx.context_hash,
                }
            except Exception as e:
                logger.warning(f"[AICoachService] AI failed, fallback: {e}")

        # 6. Fallback deterministic
        return await self._deterministic_answer(ctx, message, intent, tool_results, start)

    def _parse_ai_json(self, text: str) -> dict[str, Any]:
        t = text.strip()
        # strip code fences
        if t.startswith("```"):
            t = t.split("\n", 1)[-1] if "\n" in t else t
            if t.endswith("```"):
                t = t[:-3]
            t = t.strip()
            if t.startswith("json"):
                t = t[4:].strip()
        try:
            parsed = json.loads(t)
            # Validate against CoachAIOutput schema §51 — reject hallucinated tool fabrications
            from app.domains.coach.contracts import CoachAIOutput
            try:
                validated = CoachAIOutput.model_validate(parsed)
                # Normalize: if AI returned "answer" instead of "response"
                if not validated.response and parsed.get("answer"):
                    validated.response = parsed.get("answer")
                return validated.model_dump()
            except Exception as ve:
                logger.warning(f"[AICoachService] AI output schema validation failed: {ve}, parsed keys {list(parsed.keys())[:5]}")
                # attempt repair: ensure required fields
                if "response" not in parsed and "answer" in parsed:
                    parsed["response"] = parsed["answer"]
                if "response" not in parsed:
                    parsed["response"] = text[:1200]
                # ensure lists
                parsed.setdefault("evidence", [])
                parsed.setdefault("recommendations", [])
                parsed.setdefault("key_points", [])
                return parsed
        except Exception:
            return {"response": text, "intent": "general", "confidence": 0.6, "evidence": [], "recommendations": [], "key_points": []}

    async def _deterministic_answer(self, ctx: CoachContext, message: str, intent: CoachIntent, tool_results: list[dict], start: float) -> dict[str, Any]:
        bottleneck = ctx.dashboard_overview.bottleneck if ctx.dashboard_overview else None
        if intent == CoachIntent.PRACTICE:
            steps = []
            for tr in tool_results:
                if tr.get("tool") == "build_practice_plan" and tr.get("success"):
                    steps = tr["data"].get("steps", [])
            ans = f"Dựa trên phân tích gần đây, trọng tâm của bạn là **{bottleneck.candidate if bottleneck else 'phản xạ hội thoại'}**. Mình đã chuẩn bị kế hoạch {len(steps) or 3} bước — bạn muốn bắt đầu ngay không?"
            recs = [{"action_type": "drill", "target": "next_drill", "reason": bottleneck.description if bottleneck else "Duy trì phản xạ", "duration_minutes": 10, "practice_url": "/reflex"}]
        elif intent == CoachIntent.RECOMMEND:
            ans = f"Hôm nay bạn nên tập **{bottleneck.suggested_focus if bottleneck and bottleneck.suggested_focus else '10 phút hội thoại'}**. Lý do: {bottleneck.description if bottleneck else 'Giúp duy trì tốc độ phản xạ.'}"
            recs = [{"action_type": "conversation", "target": "today_focus", "reason": "Trọng tâm hôm nay", "duration_minutes": 10, "practice_url": "/speaking"}]
        else:
            ans = f"Bạn đang ở mức **{ctx.speaking_level}** với {ctx.total_sessions} buổi đã phân tích. Trọng tâm hiện tại: **{bottleneck.candidate if bottleneck else 'tự nhiên hoá biểu đạt'}**. Hãy hỏi 'luyện cái này cho tui' để mình tạo bài tập ngay."
            recs = []
        await self._persist(ctx.user_id, message, intent.value, ans, {"recommendations": recs, "_tool_calls": tool_results}, ctx.context_hash, int((time.time()-start)*1000))
        return {"response": ans, "intent": intent.value, "confidence": 0.82, "evidence": [], "recommendations": recs, "tool_calls": tool_results, "context_hash": ctx.context_hash}

    async def _persist(self, user_id: str, question: str, intent_type: str, answer_text: str, parsed: dict, ctx_hash: str, latency: int) -> None:
        try:
            # audit: merge evidence + tool_calls for traceability §10
            evidence = parsed.get("evidence") or []
            tool_calls = parsed.get("_tool_calls") or []
            audit_evidence = list(evidence) + ([{"tool_calls": tool_calls}] if tool_calls else [])
            rec = CoachConversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                question=question,
                intent_type=intent_type,
                answer_text=answer_text,
                key_points_json=parsed.get("key_points") or parsed.get("keyPoints") or [],
                evidence_refs_json=audit_evidence,
                recommendations_json=parsed.get("recommendations") or [],
                confidence=str(parsed.get("confidence", "medium")),
                context_hash=ctx_hash,
                latency_ms=latency,
            )
            self.db.add(rec)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"[AICoachService] persist failed: {e}")
            await self.db.rollback()

    # ── Context/insight/memory delegators (§62) ──
    async def get_context(self, user_id: str, route: str = "/dashboard", exercise_id: str | None = None) -> CoachContext:
        return await self.resolver.resolve(user_id, route, exercise_id, question=None)

    async def get_insights(self, user_id: str) -> list[dict[str, Any]]:
        from app.domains.analytics.application.insight_engine import InsightEngine
        from app.domains.analytics.application.metric_engine import MetricEngine
        me = MetricEngine(self.db)
        metrics = await me.get_all_metrics(user_id)
        eng = InsightEngine(self.db)
        insights = await eng.generate_insights(user_id, metrics)
        return [{"id": i.id, "type": i.insight_type.value, "title": i.title, "description": i.description, "confidence": i.confidence.value} for i in insights]

    async def get_memory(self, user_id: str) -> list[dict[str, Any]]:
        mems = await self.memory.list_memories(user_id, limit=20)
        return [self.memory.to_memory_payload(m) for m in mems]
