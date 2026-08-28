"""KeigoEvaluator — deterministic + AI fallback for 5 sub-modes.

Reuses language provider normalization, transformation engine candidates, Uchi/Soto, double-keigo.
"""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.japanese.provider import get_language_provider
from app.domains.keigo.double_keigo import DoubleKeigoAnalyzer
from app.domains.keigo.pragmatics import PragmaticsEngine
from app.domains.keigo.scoring import build_keigo_assessment
from app.domains.keigo.social_context import SocialContext
from app.domains.keigo.transformation_engine import KeigoTransformationEngine
from app.domains.keigo.uchi_soto import UchiSotoResolver
from app.domains.learning.prompts import LearningPrompts


def _norm(text: str) -> str:
    return re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", text.strip()) if text else ""


class KeigoEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.lang = get_language_provider()
        self.engine = KeigoTransformationEngine()
        self.uchi = UchiSotoResolver()
        self.double_analyzer = DoubleKeigoAnalyzer()
        self.pragmatics = PragmaticsEngine()

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

        # Extract keigo_config
        keigo_cfg = {}
        try:
            keigo_cfg = (exercise.extra_metadata or {}).get("keigo_config", {}) or {}
        except Exception:
            keigo_cfg = {}
        canonical = keigo_cfg.get("canonical") or (exercise.target_patterns[0] if exercise.target_patterns else None)
        accepted = keigo_cfg.get("accepted") or exercise.acceptable_variants or []
        if canonical and canonical not in accepted:
            accepted = [canonical] + accepted
        # Social context
        ctx = None
        try:
            sc_dict = keigo_cfg.get("social_context") or keigo_cfg.get("scenario_type") or {}
            if isinstance(sc_dict, dict) and sc_dict:
                ctx = SocialContext.from_dict(sc_dict)
        except Exception:
            ctx = None
        if ctx is None:
            ctx = SocialContext()

        # Timeout
        if timed_out or not raw:
            assessment = build_keigo_assessment(
                exercise_type,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                role_accuracy=0,
                register_accuracy=0,
                keigo_accuracy=0,
                grammar=0,
                naturalness=0,
                context_fit=0,
                timed_out=True,
                independence=independence,
            )
            return {
                "success": False,
                "score": assessment.overall.score,
                "assessment": assessment.to_dict(),
                "feedback": "Time's up — chưa ghi nhận phản hồi. Hãy thử Slow Mode.",
                "evidence": ["Timed out"],
                "double_keigo": None,
                "is_perfect": False,
            }

        # Deterministic check: does user answer match any accepted candidate?
        deterministic_match = False
        matched = None
        for cand in accepted:
            if _norm(cand) == norm:
                deterministic_match = True
                matched = cand
                break
            # Hiragana equivalence
            try:
                hira_user = self.lang.get_reading(raw) or norm
                hira_cand = self.lang.get_reading(cand) or _norm(cand)
                if hira_user == hira_cand:
                    deterministic_match = True
                    matched = cand
                    break
            except Exception:
                pass
        # Also canonical
        if not deterministic_match and canonical:
            if _norm(canonical) == norm:
                deterministic_match = True
                matched = canonical

        # Double keigo analysis on user text
        dk = self.double_analyzer.analyze(raw)
        # Pragmatics
        prag = self.pragmatics.evaluate(raw, ctx, None)

        # If deterministic match and no double-keigo major issue, high confidence success
        if deterministic_match and dk["status"] != "generally_inappropriate":
            # Check Uchi/Soto direction for context-sensitive modes
            role_acc = 95
            register_acc = 95
            keigo_acc = 98
            # For uchi_soto mode, verify direction
            if exercise_type == "keigo_context" or "uchi_soto" in keigo_cfg.get("sub_mode", ""):
                # Expect direction from config
                exp_dir = keigo_cfg.get("expected_direction") or keigo_cfg.get("honorific_type") or ""
                if exp_dir:
                    ok, _ = self.uchi.is_correct_direction(ctx, exp_dir)
                    role_acc = 100 if ok else 30
                    keigo_acc = 95 if ok else 35
            # Pragmatics over/under formal penalizes naturalness
            natural = prag["naturalness"] * 100
            context_fit = prag["context_fit"] * 100
            # If double keigo context_dependent, keep natural but lower confidence
            assessment = build_keigo_assessment(
                exercise_type,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                role_accuracy=role_acc,
                register_accuracy=register_acc,
                keigo_accuracy=keigo_acc,
                grammar=95,
                naturalness=natural,
                context_fit=context_fit,
                completeness=95,
                independence=independence,
                double_keigo=dk,
            )
            is_perfect = assessment.overall.score >= 80 and independence == "independent" and not late_response and dk["status"] != "generally_inappropriate"
            feedback = f"Chính xác! {matched or canonical} ✓"
            if dk["status"] == "context_dependent":
                feedback += " (lưu ý: dạng này phụ thuộc ngữ cảnh)"
            if prag["over_formal"]:
                feedback += " — hơi trang trọng quá cho ngữ cảnh, lần sau thử ngắn gọn hơn."
            return {
                "success": True,
                "score": assessment.overall.score,
                "assessment": assessment.to_dict(),
                "feedback": feedback,
                "evidence": [f"Matched: {matched}", f"Double-keigo: {dk['status']}", f"Pragmatics naturalness {natural:.0f}"],
                "double_keigo": dk,
                "is_perfect": is_perfect,
            }

        # If double keigo major issue, immediate fail even if string matches? Already handled above for match with generally_inappropriate
        if dk["status"] == "generally_inappropriate" and not deterministic_match:
            # Check if user actually produced double keigo
            # Still evaluate but mark
            pass

        # Otherwise, need AI semantic evaluation
        ai_eval = await self._ai_evaluate(exercise_type, exercise, raw, canonical, ctx, reaction_latency_ms, timer_limit_ms)
        if ai_eval:
            # Sanitize AI like reflex
            try:
                base_score = float(ai_eval.get("score", 75))
            except Exception:
                base_score = 75
            # Clamp
            base_score = max(0, min(100, base_score))
            try:
                conf = float(ai_eval.get("confidence", 0.85))
                if conf > 1:
                    conf = conf / 10 if conf <= 10 else 1.0
                conf = max(0, min(1, conf))
            except Exception:
                conf = 0.85
            # Extract dims with fallback to deterministic prag
            role_acc = float(ai_eval.get("role_accuracy", 70))
            reg_acc = float(ai_eval.get("register_accuracy", 70))
            keigo_acc = float(ai_eval.get("keigo_accuracy", ai_eval.get("grammar_score", 70)))
            natural = float(ai_eval.get("naturalness_score", prag["naturalness"]*100))
            ctx_fit = float(ai_eval.get("context_fit", prag["context_fit"]*100))
            grammar = float(ai_eval.get("grammar_score", 70))
            # Heuristic completeness for keigo: if very short (e.g., single word), penalize
            norm_len = len(norm)
            heuristic_comp = 30 if norm_len <= 2 else 55 if norm_len <= 4 else 85
            try:
                ai_comp = float(ai_eval.get("completeness", heuristic_comp))
                comp = min(ai_comp, heuristic_comp) if heuristic_comp < 50 else ai_comp
            except Exception:
                comp = heuristic_comp
            success = bool(ai_eval.get("success", True))
            # Gate: if double keigo major, force fail
            if dk["status"] == "generally_inappropriate":
                success = False
                keigo_acc = min(keigo_acc, 35)
            if comp < 50 or ctx_fit < 40:
                success = False
            assessment = build_keigo_assessment(
                exercise_type,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                role_accuracy=role_acc,
                register_accuracy=reg_acc,
                keigo_accuracy=keigo_acc,
                grammar=grammar,
                naturalness=natural,
                context_fit=ctx_fit,
                completeness=comp,
                independence=independence,
                double_keigo=dk,
            )
            # Cap score if incomplete/context wrong
            final_score = assessment.overall.score
            if comp < 50:
                final_score = min(final_score, 55)
            if ctx_fit < 40:
                final_score = min(final_score, 55)
            feedback = ai_eval.get("feedback", "Đánh giá AI")
            evidence = ai_eval.get("evidence", [f"User: {raw}"])
            if isinstance(evidence, str):
                evidence = [evidence]
            return {
                "success": success,
                "score": final_score,
                "assessment": assessment.to_dict(),
                "feedback": feedback,
                "evidence": evidence,
                "double_keigo": dk,
                "is_perfect": success and final_score >= 80 and independence == "independent",
            }

        # No AI, fallback deterministic fail
        assessment = build_keigo_assessment(
            exercise_type,
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            role_accuracy=40,
            register_accuracy=40,
            keigo_accuracy=30,
            grammar=50,
            naturalness=prag["naturalness"]*100,
            context_fit=prag["context_fit"]*100,
            completeness=40,
            independence=independence,
            double_keigo=dk,
        )
        return {
            "success": False,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": f"Chưa chính xác. Đáp án gợi ý: {canonical or accepted[0] if accepted else '—'}",
            "evidence": [f"User: {raw}", f"Expected: {canonical}", f"Double-keigo: {dk['status']}"],
            "double_keigo": dk,
            "is_perfect": False,
        }

    async def _ai_evaluate(self, sub_mode, exercise, transcript, expected, ctx, latency, timer):
        sys_inst, user_content = LearningPrompts.build_keigo_evaluation_prompt(
            sub_mode=sub_mode,
            prompt=exercise.scenario or exercise.title,
            user_transcript=transcript,
            expected=expected,
            social_context=ctx.to_dict() if ctx else None,
            linguistic_analysis={"double_keigo": self.double_analyzer.analyze(transcript)},
            reaction_latency_ms=latency,
            timer_limit_ms=timer,
        )
        req = AIRequest(
            task=AITask.KEIGO_EVALUATION,
            system_instruction=sys_inst,
            messages=[AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst), AIMessage(role=AIMessageRole.USER, content=user_content)],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.2,
            max_output_tokens=600,
            user_id=exercise.user_id,
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_EVALUATION, request=req, user_id=exercise.user_id)
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt.replace("```json", "", 1).rstrip("```").strip()
            elif txt.startswith("```"):
                txt = txt.replace("```", "", 1).rstrip("```").strip()
            parsed = json.loads(txt)
            # Sanitize
            if "confidence" in parsed:
                c = float(parsed["confidence"])
                if c > 1:
                    c = c / 10 if c <= 10 else 1.0
                parsed["confidence"] = max(0, min(1, c))
            if "evidence" in parsed and isinstance(parsed["evidence"], str):
                parsed["evidence"] = [parsed["evidence"]]
            for k in ("score", "grammar_score", "naturalness_score", "context_fit", "register_accuracy", "keigo_accuracy", "role_accuracy", "completeness"):
                if k in parsed and parsed[k] is not None:
                    try:
                        parsed[k] = max(0, min(100, float(parsed[k])))
                    except Exception:
                        pass
            return parsed
        except Exception as e:
            logger.warning(f"[KeigoEvaluator] AI eval failed: {e}")
            return None
