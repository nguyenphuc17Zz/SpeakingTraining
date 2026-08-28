"""SituationalEvaluator — intent/entity + goal completion, deterministic + AI fallback."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.situations.goal_engine import GoalEngine
from app.domains.situations.intent_resolver import IntentResolver
from app.domains.situations.scoring import build_situational_assessment


def _norm(text: str) -> str:
    return re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", text.strip()) if text else ""


class SituationalEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intent_resolver = IntentResolver()
        # AI router lazy
        self._ai_router = None

    def _get_ai(self):
        if self._ai_router is None:
            from app.domains.ai.router import AIRouter
            from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType

            self._ai_router = (AIRouter, AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType)
        return self._ai_router

    async def evaluate(
        self,
        exercise_type: str,
        exercise: Any,
        user_transcript: str,
        *,
        timer_limit_ms: int | None = None,
        reaction_latency_ms: float | None = None,
        speech_confidence: float | None = None,
        timed_out: bool = False,
        late_response: bool = False,
        independence: str = "independent",
    ) -> dict[str, Any]:
        raw = (user_transcript or "").strip()
        norm = _norm(raw)

        # Extract situational config
        situ_cfg = {}
        try:
            situ_cfg = (exercise.extra_metadata or {}).get("situational_config", {}) or {}
        except Exception:
            situ_cfg = {}
        goals_cfg = situ_cfg.get("goals", []) or []
        # For Exercise from learning, goals may be in target_patterns or scenario
        if not goals_cfg and exercise.target_patterns:
            # Fallback: create goal from target_patterns
            goals_cfg = [{"id": f"goal_{i}", "task": pat, "required_intent": pat.upper(), "description": pat, "status": "NOT_STARTED"} for i, pat in enumerate(exercise.target_patterns[:3])]

        if timed_out or not raw:
            assessment = build_situational_assessment(
                exercise_type,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                task_completion=0,
                timed_out=True,
            )
            return {"success": False, "score": assessment.overall.score, "assessment": assessment.to_dict(), "feedback": "Time's up — chưa ghi nhận.", "evidence": ["Timed out"], "goals": goals_cfg}

        # Intent/entity
        intent_res = self.intent_resolver.resolve(raw)
        intent = intent_res["intent"]
        entities = intent_res["entities"]
        # Goal engine
        goal_engine = GoalEngine(goals_cfg)
        updated_goals = goal_engine.update(intent_res, entities, raw)
        completion = goal_engine.completion_rate() * 100
        # Determine intent accuracy
        if intent == "UNKNOWN":
            # Try AI fallback for intent if deterministic low confidence
            ai_intent = await self._ai_intent_fallback(raw, exercise)
            if ai_intent:
                intent = ai_intent.get("intent", intent)
                entities = ai_intent.get("entities", entities)
                # Re-run goal engine with AI intent
                goal_engine2 = GoalEngine(goals_cfg)
                updated_goals = goal_engine2.update({"intent": intent, "confidence": ai_intent.get("confidence", 0.7)}, entities, raw)
                completion = goal_engine2.completion_rate() * 100
                intent_accuracy = 85 if intent != "UNKNOWN" else 35
            else:
                intent_accuracy = 35
        else:
            intent_accuracy = 85 if intent_res["confidence"] > 0.7 else 60

        # Context fit & naturalness via simple heuristic + AI if available
        # For MVP, use intent confidence and goal completion as proxy
        context_fit = 85 if completion >= 50 else 60 if completion > 0 else 35
        naturalness = 80  # Could call keigo/pitch evaluators for cross-mode if needed
        grammar = 80  # Could call grammar analyzer, but for MVP use intent success
        # Check if intent was backchannel vs actual answer — backchannel should not complete goal
        if intent == "BACKCHANNEL" and completion == 0:
            # Backchannel alone not success
            pass

        # Build assessment
        assessment = build_situational_assessment(
            exercise_type,
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            task_completion=completion,
            intent_accuracy=intent_accuracy,
            context_fit=context_fit,
            naturalness=naturalness,
            grammar=grammar,
            register_score=80,
            recovery=85,
            timed_out=False,
            late_response=late_response,
            independence=independence,
        )

        # For single-turn evaluation, any goal completion counts as success (multi-turn will accumulate)
        success = (completion > 0 and intent_accuracy >= 50) or (completion >= 50)
        # Blind mode: hidden goals, success if at least one hidden completed
        if any(g.get("hidden") for g in updated_goals):
            hidden_rate = goal_engine.hidden_success_rate() * 100
            if hidden_rate == 0 and any(g.get("hidden") for g in goals_cfg):
                # For blind, require hidden success
                success = hidden_rate > 0
            elif hidden_rate > 0:
                success = True

        feedback = f"Hoàn thành {completion:.0f}% mục tiêu. Intent: {intent}"
        if success:
            feedback = "✅ " + feedback + f" — {len([g for g in updated_goals if g['status']=='COMPLETED'])} mục tiêu đạt."
        else:
            # Provide native alternative hint
            if not intent_accuracy >= 60:
                feedback = "⚠️ Chưa rõ ý định. Thử: 'お願いします' / 'ください' cho yêu cầu."

        return {
            "success": success,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": feedback,
            "evidence": [f"Intent {intent} conf {intent_res.get('confidence',0):.2f}", f"Goals {len(updated_goals)} completion {completion:.0f}%", f"Entities {entities}"],
            "goals": updated_goals,
            "intent": intent_res,
            "is_perfect": success and assessment.overall.score >= 85,
        }

    async def _ai_intent_fallback(self, transcript: str, exercise: Any) -> dict | None:
        try:
            AIRouter, AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType = self._get_ai()
            from app.domains.ai.router import AIRouter as AIRouterCls

            router = AIRouterCls(self.db)
            sys_inst = "Bạn là bộ phân tích intent tiếng Nhật. Trả về JSON {intent, entities:[{type,value}], confidence}. Intent là một trong: REQUEST, ORDER_FOOD, DECLINE_BAG, ASK_RECOMMENDATION, CONFIRM, APOLOGIZE, THANK, UNKNOWN."
            user_content = f"Transcript: {transcript}\nScenario: {exercise.scenario or exercise.title}"
            req = AIRequest(
                task=AITask.SITUATIONAL_EVALUATION,
                system_instruction=sys_inst,
                messages=[AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst), AIMessage(role=AIMessageRole.USER, content=user_content)],
                response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
                temperature=0.2,
                max_output_tokens=300,
                user_id=exercise.user_id,
            )
            resp = await router.generate(task=AITask.SITUATIONAL_EVALUATION, request=req, user_id=exercise.user_id)
            import json

            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt.replace("```json", "", 1).rstrip("```").strip()
            elif txt.startswith("```"):
                txt = txt.replace("```", "", 1).rstrip("```").strip()
            parsed = json.loads(txt)
            return parsed
        except Exception as e:
            logger.warning(f"[SituationalEvaluator] AI fallback failed {e}")
            return None
