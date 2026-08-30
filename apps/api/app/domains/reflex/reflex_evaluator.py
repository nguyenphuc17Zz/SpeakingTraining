"""Reflex evaluator — deterministic conjugation + semantic AI evaluation.

Hybrid: conjugation via JapaneseConjugationEngine, open-ended via AIRouter reuse.
"""

from __future__ import annotations

import json
import re
import difflib
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine
from app.domains.reflex.scoring import ReflexScoringPolicy


def _normalize_japanese(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", t)
    return t


def _strip_filler(text: str) -> str:
    # Common fillers to detect thinking stall
    fillers = ["えーと", "えっと", "あの", "なんか", "まあ", "その"]
    t = text.strip()
    for f in fillers:
        if t.startswith(f):
            t = t[len(f):].lstrip(" 、,")
    return t


class ReflexEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.conj = JapaneseConjugationEngine()

    async def evaluate_conjugation(
        self,
        verb: str,
        target_form: str,
        user_transcript: str,
        *,
        timer_limit_ms: int | None = None,
        reaction_latency_ms: float | None = None,
        semantic_latency_ms: float | None = None,
        speech_confidence: float | None = None,
        timed_out: bool = False,
        late_response: bool = False,
        independence: str = "independent",
    ) -> dict[str, Any]:
        raw = (user_transcript or "").strip()
        normalized = _normalize_japanese(raw)

        if timed_out or not raw:
            assessment = ReflexScoringPolicy.build(
                "reflex_conjugation",
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                accuracy_score=0.0,
                naturalness_score=0.0,
                fluency_score=0.0,
                timed_out=True,
                independence_level=independence,
            )
            return {
                "success": False,
                "score": assessment.overall.score,
                "assessment": assessment.to_dict(),
                "feedback": "Time's up — chưa ghi nhận phản hồi. Hãy thử lại với Slow Mode hoặc xem gợi ý.",
                "evidence": ["No speech detected within timer"],
                "conjugation": {"is_correct": False, "canonical": "", "accepted": []},
                "transcript": raw,
                "normalized": normalized,
            }

        val = self.conj.validate(verb, target_form, raw, normalize=True)
        is_correct = val["is_correct"]
        accuracy = 100.0 if is_correct else 25.0
        # Fluency: if correct and reaction fast → higher
        fluency = 85.0 if is_correct else 40.0
        if is_correct and reaction_latency_ms is not None and timer_limit_ms:
            ratio = reaction_latency_ms / timer_limit_ms
            if ratio < 0.5:
                fluency = 95.0
            elif ratio < 0.7:
                fluency = 85.0

        assessment = ReflexScoringPolicy.build(
            "reflex_conjugation",
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            accuracy_score=accuracy,
            naturalness_score=accuracy,  # conjugation naturalness = accuracy
            fluency_score=fluency,
            context_fit_score=accuracy,
            completeness_score=100.0 if is_correct else 30.0,
            timed_out=False,
            late_response=late_response,
            semantic_latency_ms=semantic_latency_ms,
            independence_level=independence,
        )
        # Perfect check
        is_perfect = is_correct and assessment.overall.score >= 80 and independence == "independent" and not late_response and not timed_out

        if is_correct:
            fb = f"Perfect! {verb} → {val['canonical']} (phản ứng {reaction_latency_ms:.0f}ms)" if reaction_latency_ms else f"Chính xác! {val['canonical']}"
        else:
            fb = f"Chưa chính xác. Đáp án: {val['canonical']}"
            if val["accepted"] and len(val["accepted"]) > 1:
                fb += f" (cũng chấp nhận: {', '.join(val['accepted'])})"
            if val.get("variant_notes"):
                fb += f" — {'; '.join(val['variant_notes'])}"

        return {
            "success": is_correct,
            "is_perfect": is_perfect,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": fb,
            "evidence": [f"User: {raw}", f"Expected: {val['canonical']}", f"Matched: {val.get('matched')}" if is_correct else "No match"],
            "conjugation": val,
            "transcript": raw,
            "normalized": normalized,
        }

    async def evaluate_transformation(
        self,
        source: str,
        task: str,
        expected: str,
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
        normalized = _normalize_japanese(raw)
        expected_norm = _normalize_japanese(expected)
        if timed_out or not raw:
            assessment = ReflexScoringPolicy.build(
                "reflex_transformation",
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                accuracy_score=0.0,
                timed_out=True,
                independence_level=independence,
            )
            return {"success": False, "score": assessment.overall.score, "assessment": assessment.to_dict(), "feedback": "Time's up — chưa ghi nhận phản hồi.", "evidence": ["No speech"], "transcript": raw, "normalized": normalized}

        # Deterministic check first
        exact_match = normalized == expected_norm
        # Use AI for semantic preservation if not exact
        ai_eval = None
        if not exact_match:
            ai_eval = await self._ai_evaluate(
                title="Sentence Transformation",
                objective=f"Transform '{source}' with task '{task}'",
                target_patterns=[expected],
                user_transcript=raw,
                context=f"Source: {source} | Task: {task} | Expected: {expected}",
                task=AITask.REFLEX_EVALUATION,
            )
        if exact_match:
            accuracy = 100.0
            success = True
            feedback = f"Chính xác! → {expected}"
        elif ai_eval:
            accuracy = float(ai_eval.get("score", 60))
            success = bool(ai_eval.get("success", False)) or accuracy >= 75
            feedback = ai_eval.get("feedback", "Đánh giá AI")
        else:
            accuracy = 55.0
            success = False
            feedback = f"Chưa khớp đáp án mẫu. Kỳ vọng: {expected}"

        assessment = ReflexScoringPolicy.build(
            "reflex_transformation",
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            accuracy_score=accuracy,
            timed_out=False,
            late_response=late_response,
            independence_level=independence,
        )
        return {
            "success": success,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": feedback,
            "evidence": [f"Source: {source}", f"Task: {task}", f"Expected: {expected}", f"User: {raw}"],
            "transcript": raw,
            "normalized": normalized,
        }

    async def evaluate_qna_or_context(
        self,
        sub_mode: str,
        prompt: str,
        user_transcript: str,
        *,
        semantic_target: dict[str, Any] | None = None,
        timer_limit_ms: int | None = None,
        reaction_latency_ms: float | None = None,
        semantic_latency_ms: float | None = None,
        speech_confidence: float | None = None,
        timed_out: bool = False,
        late_response: bool = False,
        independence: str = "independent",
    ) -> dict[str, Any]:
        raw = (user_transcript or "").strip()
        normalized = _normalize_japanese(raw)
        # Detect thinking stall: filler before meaningful content
        stripped = _strip_filler(raw)
        thinking_stall = len(raw) != len(stripped)

        if timed_out or not raw:
            assessment = ReflexScoringPolicy.build(
                sub_mode,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                accuracy_score=0.0,
                timed_out=True,
                independence_level=independence,
            )
            return {"success": False, "score": assessment.overall.score, "assessment": assessment.to_dict(), "feedback": "Time's up — chưa ghi nhận phản hồi.", "evidence": ["No speech"], "transcript": raw, "normalized": normalized}

        # Short/canned answer check
        completeness = 100.0
        if len(normalized) < 3 or raw.strip() in ("映画。", "はい。", "いいえ。"):
            completeness = 30.0

        ai_eval = await self._ai_evaluate(
            title="Speed Q&A" if sub_mode == "reflex_qna" else "Contextual Reaction",
            objective=prompt,
            target_patterns=[],
            user_transcript=raw,
            context=f"Prompt: {prompt} | Target: {semantic_target}",
            task=AITask.REFLEX_EVALUATION,
        )
        if ai_eval:
            accuracy = float(ai_eval.get("grammar_score", ai_eval.get("score", 70)))
            naturalness = float(ai_eval.get("naturalness_score", accuracy))
            context_fit = float(ai_eval.get("context_fit", 70))
            # AI returns context_fit indirectly via score if not detailed
            if "context_fit" not in ai_eval and ai_eval.get("target_usage") == "incorrect":
                context_fit = 30.0
            success = bool(ai_eval.get("success", True)) and completeness > 50
            # Completeness gate: if AI says incomplete, respect it
            if ai_eval.get("completeness", 100) < 50:
                completeness = float(ai_eval.get("completeness"))
                success = False
            feedback = ai_eval.get("feedback", "Đánh giá AI")
            evidence = ai_eval.get("evidence", [f"Prompt: {prompt}", f"User: {raw}"])
        else:
            # Fallback heuristic
            accuracy = 70.0 if completeness > 50 else 45.0
            naturalness = accuracy
            context_fit = accuracy
            success = completeness > 50
            feedback = "Phản hồi đã ghi nhận (AI evaluator tạm offline, dùng heuristic)."
            evidence = [f"Prompt: {prompt}", f"User: {raw}"]

        assessment = ReflexScoringPolicy.build(
            sub_mode,
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            accuracy_score=accuracy,
            naturalness_score=naturalness,
            fluency_score=75.0,  # could be derived from STT fluency later
            context_fit_score=context_fit,
            completeness_score=completeness,
            timed_out=False,
            late_response=late_response,
            semantic_latency_ms=semantic_latency_ms,
            independence_level=independence,
        )
        # Cap overall if context mismatch despite grammar ok
        if context_fit < 40 and accuracy > 70:
            success = False

        return {
            "success": success,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": feedback,
            "evidence": evidence,
            "transcript": raw,
            "normalized": normalized,
            "thinking_stall": thinking_stall,
        }

    async def evaluate_vocabulary(
        self,
        word: str,
        direction: str,
        word_reading: str,
        word_meaning_vi: str,
        synonyms_vi: list[str],
        user_transcript: str,
        *,
        timer_limit_ms: int | None = None,
        reaction_latency_ms: float | None = None,
        semantic_latency_ms: float | None = None,
        speech_confidence: float | None = None,
        timed_out: bool = False,
        late_response: bool = False,
        independence: str = "independent",
    ) -> dict[str, Any]:
        """Evaluate vocabulary recall: ja→vi (fuzzy meaning match) or vi→ja (exact word/reading match)."""
        raw = (user_transcript or "").strip()
        normalized = _normalize_japanese(raw)

        if timed_out or not raw:
            assessment = ReflexScoringPolicy.build(
                "reflex_vocabulary",
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                accuracy_score=0.0,
                timed_out=True,
                independence_level=independence,
            )
            return {
                "success": False,
                "score": assessment.overall.score,
                "assessment": assessment.to_dict(),
                "feedback": "Time's up — chưa ghi nhận phản hồi. Đáp án: " + (word_meaning_vi if direction == "ja_to_vi" else word),
                "evidence": ["No speech detected"],
                "transcript": raw,
                "normalized": normalized,
                "direction": direction,
            }

        is_correct = False
        feedback = ""

        if direction == "ja_to_vi":
            # Fuzzy Vietnamese meaning match
            all_accepted = [word_meaning_vi] + synonyms_vi
            raw_lower = raw.lower().strip()
            # 1. Exact match check
            for accepted in all_accepted:
                if raw_lower == accepted.lower().strip():
                    is_correct = True
                    break
            # 2. Fuzzy match — threshold 0.75 similarity
            if not is_correct:
                for accepted in all_accepted:
                    ratio = difflib.SequenceMatcher(None, raw_lower, accepted.lower()).ratio()
                    if ratio >= 0.75:
                        is_correct = True
                        break
            # 3. Contains check (user says partial but correct key)
            if not is_correct:
                for accepted in all_accepted:
                    key_words = [w for w in accepted.lower().split() if len(w) >= 3]
                    if key_words and all(kw in raw_lower for kw in key_words):
                        is_correct = True
                        break

            if is_correct:
                feedback = f"Chính xác! {word} ({word_reading}) = {word_meaning_vi}"
            else:
                feedback = f"Chưa đúng. {word} ({word_reading}) = {word_meaning_vi}"
                if synonyms_vi:
                    feedback += f" (cũng accept: {', '.join(synonyms_vi)})"

        else:  # vi_to_ja
            # Exact Japanese word or reading match (normalize kana)
            raw_norm = _normalize_japanese(raw)
            word_norm = _normalize_japanese(word)
            reading_norm = _normalize_japanese(word_reading)
            is_correct = raw_norm == word_norm or raw_norm == reading_norm
            # Fuzzy fallback for slight mis-readings
            if not is_correct and len(word_norm) > 1:
                ratio_word = difflib.SequenceMatcher(None, raw_norm, word_norm).ratio()
                ratio_read = difflib.SequenceMatcher(None, raw_norm, reading_norm).ratio()
                if max(ratio_word, ratio_read) >= 0.85:
                    is_correct = True

            if is_correct:
                feedback = f"Chính xác! {word_meaning_vi} → {word} ({word_reading})"
            else:
                feedback = f"Chưa đúng. {word_meaning_vi} → {word} ({word_reading})"

        accuracy = 100.0 if is_correct else 20.0
        fluency = 90.0 if is_correct else 40.0
        if is_correct and reaction_latency_ms is not None and timer_limit_ms:
            ratio = reaction_latency_ms / timer_limit_ms
            fluency = 95.0 if ratio < 0.5 else (85.0 if ratio < 0.7 else 75.0)

        assessment = ReflexScoringPolicy.build(
            "reflex_vocabulary",
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            accuracy_score=accuracy,
            naturalness_score=accuracy,
            fluency_score=fluency,
            context_fit_score=accuracy,
            completeness_score=100.0 if is_correct else 20.0,
            timed_out=False,
            late_response=late_response,
            semantic_latency_ms=semantic_latency_ms,
            independence_level=independence,
        )
        is_perfect = is_correct and assessment.overall.score >= 80 and independence == "independent" and not late_response

        return {
            "success": is_correct,
            "is_perfect": is_perfect,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": feedback,
            "evidence": [f"User: {raw}", f"Expected: {word_meaning_vi if direction == 'ja_to_vi' else word}"],
            "transcript": raw,
            "normalized": normalized,
            "direction": direction,
            "word": word,
            "word_reading": word_reading,
            "word_meaning_vi": word_meaning_vi,
        }

    async def evaluate_keigo_vocabulary(
        self,
        source_word: str,
        target_type: str,
        target_label_vi: str,
        canonical: str,
        acceptable_variants: list[str],
        user_transcript: str,
        *,
        timer_limit_ms: int | None = None,
        reaction_latency_ms: float | None = None,
        semantic_latency_ms: float | None = None,
        speech_confidence: float | None = None,
        timed_out: bool = False,
        late_response: bool = False,
        independence: str = "independent",
    ) -> dict[str, Any]:
        """Evaluate rapid Keigo word transformation (Plain -> Sonkeigo/Kenjougo/Business)."""
        raw = (user_transcript or "").strip()
        normalized = _normalize_japanese(raw)

        if timed_out or not raw:
            assessment = ReflexScoringPolicy.build(
                "reflex_keigo_vocab",
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                accuracy_score=0.0,
                timed_out=True,
                independence_level=independence,
            )
            return {
                "success": False,
                "score": assessment.overall.score,
                "assessment": assessment.to_dict(),
                "feedback": f"Time's up — chưa ghi nhận phản hồi. Đáp án: {canonical}",
                "evidence": ["No speech detected"],
                "transcript": raw,
                "normalized": normalized,
                "target_type": target_type,
            }

        # Normalize candidates
        all_candidates = [canonical] + [v for v in acceptable_variants if v != canonical]
        norm_candidates = [_normalize_japanese(c) for c in all_candidates]

        is_correct = False
        matched_text = ""

        # 1. Exact match
        for cand, norm_cand in zip(all_candidates, norm_candidates):
            if normalized == norm_cand:
                is_correct = True
                matched_text = cand
                break

        # 2. Fuzzy match (threshold 0.85)
        if not is_correct:
            for cand, norm_cand in zip(all_candidates, norm_candidates):
                ratio = difflib.SequenceMatcher(None, normalized, norm_cand).ratio()
                if ratio >= 0.85:
                    is_correct = True
                    matched_text = cand
                    break

        if is_correct:
            feedback = f"Chính xác! {source_word} → {canonical} ✓"
        else:
            fb_extra = f" (cũng chấp nhận: {', '.join(acceptable_variants[:3])})" if acceptable_variants else ""
            feedback = f"Chưa chính xác. {source_word} sang {target_label_vi} là: {canonical}{fb_extra}"

        accuracy = 100.0 if is_correct else 25.0
        fluency = 90.0 if is_correct else 35.0
        if is_correct and reaction_latency_ms is not None and timer_limit_ms:
            ratio = reaction_latency_ms / timer_limit_ms
            fluency = 95.0 if ratio < 0.5 else (85.0 if ratio < 0.7 else 75.0)

        assessment = ReflexScoringPolicy.build(
            "reflex_keigo_vocab",
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            accuracy_score=accuracy,
            naturalness_score=accuracy,
            fluency_score=fluency,
            context_fit_score=accuracy,
            completeness_score=100.0 if is_correct else 25.0,
            timed_out=False,
            late_response=late_response,
            semantic_latency_ms=semantic_latency_ms,
            independence_level=independence,
        )
        is_perfect = is_correct and assessment.overall.score >= 80 and independence == "independent" and not late_response

        return {
            "success": is_correct,
            "is_perfect": is_perfect,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": feedback,
            "evidence": [f"User: {raw}", f"Target: {target_label_vi}", f"Expected: {canonical}"],
            "transcript": raw,
            "normalized": normalized,
            "target_type": target_type,
            "source_word": source_word,
            "canonical": canonical,
            "matched": matched_text,
        }

    async def _ai_evaluate(self, title: str, objective: str, target_patterns: list[str], user_transcript: str, context: str | None, task: AITask) -> dict[str, Any] | None:

        from app.domains.learning.prompts import LearningPrompts
        sys_inst, user_content = LearningPrompts.build_exercise_evaluation_prompt(
            exercise_title=title,
            exercise_objective=objective,
            target_patterns=target_patterns,
            user_transcript=user_transcript,
            context_notes=context,
        )
        # Extend sys_inst for reflex specifics
        sys_inst += "\nBạn đang đánh giá bài REFLEX (phản xạ nhanh). Hãy xét context_fit, completeness, naturalness riêng. Đừng chỉ chấm ngữ pháp."
        req = AIRequest(
            task=task,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.2,
            max_output_tokens=600,
        )
        try:
            # Need user_id for router; use dummy if not available in this path (will be overridden by caller)
            resp = await self.ai_router.generate(task=task, request=req, user_id="reflex_eval")
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt.replace("```json", "", 1).rstrip("```").strip()
            elif txt.startswith("```"):
                txt = txt.replace("```", "", 1).rstrip("```").strip()
            return json.loads(txt)
        except Exception as e:
            logger.warning(f"[ReflexEvaluator] AI eval failed: {e}")
            return None
