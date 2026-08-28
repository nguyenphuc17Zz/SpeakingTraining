import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.learning.contracts import ExerciseResult, IndependenceLevel
from app.domains.learning.models import Exercise, ExerciseAttempt
from app.domains.learning.prompts import LearningPrompts


class ExerciseEvaluator:
    """Evaluates learner exercise attempts using a hybrid of deterministic rules, Phase 4/6 signals, and AI assessment."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def evaluate_attempt(
        self,
        exercise: Exercise,
        attempt: ExerciseAttempt,
        user_transcript: str,
        turn_analysis_score: float | None = None,
        pronunciation_score: float | None = None,
        response_speed_ms: float | None = None,
        used_hint: bool = False,
        reflex_metrics: dict[str, Any] | None = None,
        keigo_metrics: dict[str, Any] | None = None,
        pitch_metrics: dict[str, Any] | None = None,
        situational_metrics: dict[str, Any] | None = None,
    ) -> ExerciseResult:
        """
        Comprehensive assessment combining linguistic correctness, target pattern presence,
        naturalness, pronunciation, and independence.
        """
        transcript_clean = user_transcript.strip()
        transcript_no_punct = re.sub(r"[。！？、\s\!\?\,\.]+", "", transcript_clean)
        target_patterns = exercise.target_patterns or []

        # Determine independence level
        if used_hint or exercise.scaffold_level != "none":
            indep = IndependenceLevel.ASSISTED_HINT
        else:
            indep = IndependenceLevel.INDEPENDENT

        # Strict Empty Audio / Missing Speech Check (0% score, no fake points)
        # Check reflex/keigo/pitch/situational timed_out if provided (alias) — merge all
        _reflex: dict[str, Any] = {}
        if situational_metrics:
            _reflex.update(situational_metrics)
        if pitch_metrics:
            _reflex.update(pitch_metrics)
        if keigo_metrics:
            _reflex.update(keigo_metrics)
        if reflex_metrics:
            _reflex.update(reflex_metrics)
        _timed_out = bool(_reflex.get("timed_out"))
        _late = bool(_reflex.get("late_response"))
        if not transcript_clean:
            # Timed out vs no speech are different states
            if _timed_out:
                fb = "Time's up — hết giờ mà chưa ghi nhận phản hồi. Hãy thử Slow Mode hoặc xem gợi ý."
            else:
                fb = "Không nhận diện được giọng nói trong bản thu âm. Vui lòng kiểm tra micro hoặc nói to rõ hơn."
            return ExerciseResult(
                exercise_id=exercise.id,
                user_id=exercise.user_id,
                score=0.0,
                success=False,
                confidence=1.0,
                independence=indep,
                target_usage="not_attempted",
                feedback=fb,
                evidence=["Không phát hiện âm thanh giọng nói từ Whisper STT." + (" Timed out." if _timed_out else "")],
                grammar_score=0.0,
                naturalness_score=0.0,
                pronunciation_score=pronunciation_score or 0.0,
                metrics={
                    "pattern_found": False,
                    "used_hint": used_hint,
                    "response_speed_ms": response_speed_ms,
                    "grammar_score": 0.0,
                    "naturalness_score": 0.0,
                    "pronunciation_score": pronunciation_score,
                    "reflex": _reflex,
                } if _reflex else None,
            )

        # Keigo branch: delegate to KeigoEvaluator if exercise_type startswith keigo
        if exercise.exercise_type.startswith("keigo"):
            try:
                from app.domains.keigo.evaluator import KeigoEvaluator

                keigo_eval = KeigoEvaluator(self.db)
                k_res = await keigo_eval.evaluate(
                    exercise_type=exercise.exercise_type,
                    exercise=exercise,
                    user_transcript=user_transcript,
                    timer_limit_ms=_reflex.get("timer_limit_ms"),
                    reaction_latency_ms=_reflex.get("reaction_latency_ms", response_speed_ms),
                    speech_confidence=_reflex.get("speech_confidence"),
                    timed_out=_timed_out,
                    late_response=_late,
                    independence=_reflex.get("independence") or ("assisted_hint" if used_hint else "independent"),
                )
                # Map KeigoEvaluator result to ExerciseResult
                _lat = _reflex.get("reaction_latency_ms", response_speed_ms)
                _keigo_metrics = {
                    "pattern_found": k_res["success"],
                    "used_hint": used_hint,
                    "response_speed_ms": response_speed_ms,
                    "keigo": _reflex,
                    "reaction_latency_ms": _lat,
                    "timer_limit_ms": _reflex.get("timer_limit_ms"),
                    "timed_out": _timed_out,
                    "late_response": _late,
                    "keigo_accuracy": k_res["assessment"]["keigo_accuracy"]["score"] if k_res.get("assessment") else 0,
                    "role_accuracy": k_res["assessment"]["role_accuracy"]["score"] if k_res.get("assessment") else 0,
                    "double_keigo": k_res.get("double_keigo"),
                }
                # Merge into metrics
                return ExerciseResult(
                    exercise_id=exercise.id,
                    user_id=exercise.user_id,
                    score=float(k_res["score"]),
                    success=bool(k_res["success"]),
                    confidence=float(k_res["assessment"]["overall"]["confidence"] if k_res.get("assessment") and "overall" in k_res["assessment"] else 0.85),
                    target_mastery_delta={},
                    feedback=k_res["feedback"],
                    evidence=k_res["evidence"],
                    metrics=_keigo_metrics,
                    independence=IndependenceLevel.ASSISTED_HINT if used_hint else IndependenceLevel.INDEPENDENT,
                    response_speed_ms=response_speed_ms,
                    target_usage="correct" if k_res["success"] else "incorrect",
                    grammar_score=float(k_res["assessment"]["grammar"]["score"] if k_res.get("assessment") else 70),
                    naturalness_score=float(k_res["assessment"]["naturalness"]["score"] if k_res.get("assessment") else 70),
                    attempt_id=attempt.id,
                )
            except Exception as e:
                logger.warning(f"[ExerciseEvaluator] Keigo branch failed, fallback to generic: {e}")
                # Fall through to generic

        # Pitch branch: delegate to PitchEvaluator if exercise_type is pitch-related
        if exercise.exercise_type.startswith("pitch") or exercise.exercise_type in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition", "pitch_minimal_pair"):
            try:
                from app.domains.pitch.evaluator import PitchEvaluator

                pitch_eval = PitchEvaluator(self.db)
                p_res = await pitch_eval.evaluate(
                    exercise_type=exercise.exercise_type,
                    exercise=exercise,
                    user_transcript=user_transcript,
                    timer_limit_ms=_reflex.get("timer_limit_ms"),
                    reaction_latency_ms=_reflex.get("reaction_latency_ms", response_speed_ms),
                    speech_confidence=_reflex.get("speech_confidence"),
                    pitch_confidence=_reflex.get("pitch_confidence") or _reflex.get("speech_confidence"),
                    audio_quality=_reflex.get("audio_quality"),
                    timed_out=_timed_out,
                    late_response=_late,
                    independence=_reflex.get("independence") or ("assisted_hint" if used_hint else "independent"),
                    audio_samples=None,  # TODO: pass raw audio when available via pitch_metrics
                )
                # Map PitchEvaluator result to ExerciseResult
                _lat = _reflex.get("reaction_latency_ms", response_speed_ms)
                _pitch_metrics = {
                    "pattern_found": p_res["success"],
                    "used_hint": used_hint,
                    "response_speed_ms": response_speed_ms,
                    "pitch": _reflex,
                    "reaction_latency_ms": _lat,
                    "timer_limit_ms": _reflex.get("timer_limit_ms"),
                    "timed_out": _timed_out,
                    "late_response": _late,
                    "pitch_confidence": _reflex.get("pitch_confidence"),
                    "audio_quality": _reflex.get("audio_quality"),
                }
                # Handle retry audio status
                if p_res.get("status") == "RETRY_AUDIO":
                    return ExerciseResult(
                        exercise_id=exercise.id,
                        user_id=exercise.user_id,
                        score=0.0,
                        success=False,
                        confidence=0.3,
                        target_mastery_delta={},
                        feedback=p_res["feedback"],
                        evidence=p_res["evidence"],
                        metrics=_pitch_metrics,
                        independence=IndependenceLevel.ASSISTED_HINT if used_hint else IndependenceLevel.INDEPENDENT,
                        response_speed_ms=response_speed_ms,
                        target_usage="not_attempted",
                        pronunciation_score=pronunciation_score,
                        grammar_score=0.0,
                        naturalness_score=0.0,
                        attempt_id=attempt.id,
                    )
                return ExerciseResult(
                    exercise_id=exercise.id,
                    user_id=exercise.user_id,
                    score=float(p_res["score"]),
                    success=bool(p_res["success"]),
                    confidence=float(p_res["assessment"]["overall"]["confidence"] if p_res.get("assessment") and "overall" in p_res["assessment"] else 0.85) if isinstance(p_res.get("assessment"), dict) else 0.85,
                    target_mastery_delta={},
                    feedback=p_res["feedback"],
                    evidence=p_res["evidence"],
                    metrics={**_pitch_metrics, "pitch_assessment": p_res.get("assessment")},
                    independence=IndependenceLevel.ASSISTED_HINT if used_hint else IndependenceLevel.INDEPENDENT,
                    response_speed_ms=response_speed_ms,
                    target_usage="correct" if p_res["success"] else "incorrect",
                    grammar_score=float(p_res["assessment"]["accent_pattern"]["score"] if p_res.get("assessment") and "accent_pattern" in p_res["assessment"] else 70),
                    naturalness_score=float(p_res["assessment"]["contour"]["score"] if p_res.get("assessment") and "contour" in p_res["assessment"] else 70),
                    attempt_id=attempt.id,
                )
            except Exception as e:
                logger.warning(f"[ExerciseEvaluator] Pitch branch failed, fallback to generic: {e}")

        # Situational branch: delegate to SituationalEvaluator if situational
        if exercise.exercise_type.startswith("situational"):
            try:
                from app.domains.situations.evaluator import SituationalEvaluator

                situ_eval = SituationalEvaluator(self.db)
                s_res = await situ_eval.evaluate(
                    exercise_type=exercise.exercise_type,
                    exercise=exercise,
                    user_transcript=user_transcript,
                    timer_limit_ms=_reflex.get("timer_limit_ms"),
                    reaction_latency_ms=_reflex.get("reaction_latency_ms", response_speed_ms),
                    speech_confidence=_reflex.get("speech_confidence"),
                    timed_out=_timed_out,
                    late_response=_late,
                    independence=_reflex.get("independence") or ("assisted_hint" if used_hint else "independent"),
                )
                _lat = _reflex.get("reaction_latency_ms", response_speed_ms)
                _situ_metrics = {
                    "pattern_found": s_res["success"],
                    "used_hint": used_hint,
                    "response_speed_ms": response_speed_ms,
                    "situational": _reflex,
                    "reaction_latency_ms": _lat,
                    "timer_limit_ms": _reflex.get("timer_limit_ms"),
                    "timed_out": _timed_out,
                    "late_response": _late,
                }
                return ExerciseResult(
                    exercise_id=exercise.id,
                    user_id=exercise.user_id,
                    score=float(s_res["score"]),
                    success=bool(s_res["success"]),
                    confidence=float(s_res["assessment"]["overall"]["confidence"] if s_res.get("assessment") and "overall" in s_res["assessment"] else 0.85) if isinstance(s_res.get("assessment"), dict) else 0.85,
                    target_mastery_delta={},
                    feedback=s_res["feedback"],
                    evidence=s_res["evidence"],
                    metrics={**_situ_metrics, "situational_assessment": s_res.get("assessment"), "goals": s_res.get("goals")},
                    independence=IndependenceLevel.ASSISTED_HINT if used_hint else IndependenceLevel.INDEPENDENT,
                    response_speed_ms=response_speed_ms,
                    target_usage="correct" if s_res["success"] else "incorrect",
                    grammar_score=float(s_res["assessment"]["grammar"]["score"] if s_res.get("assessment") and "grammar" in s_res["assessment"] else 70),
                    naturalness_score=float(s_res["assessment"]["naturalness"]["score"] if s_res.get("assessment") and "naturalness" in s_res["assessment"] else 70),
                    attempt_id=attempt.id,
                )
            except Exception as e:
                logger.warning(f"[ExerciseEvaluator] Situational branch failed, fallback to generic: {e}")

        # Reflex deterministic branch: if exercise is reflex_conjugation, try conjugation engine first
        is_reflex_conj = exercise.exercise_type == "reflex_conjugation"
        conj_result = None
        if is_reflex_conj and exercise.extra_metadata:
            try:
                from app.domains.reflex.conjugation_engine import JapaneseConjugationEngine
                _verb = (exercise.extra_metadata.get("reflex_config", {}) or {}).get("verb") or (exercise.target_patterns[0] if target_patterns else "")
                _form = (exercise.extra_metadata.get("reflex_config", {}) or {}).get("conjugation_target") or "dictionary"
                # Heuristic: extract verb from scenario/prompt if not in metadata
                if not _verb:
                    _verb = exercise.scenario or exercise.title or ""
                    # try to extract kanji verb
                    import re as _re
                    m = _re.search(r"[\u4e00-\u9faf]+[くすつぬぶむるぐう]+|[\u3040-\u309f]+る|する|来る|くる", _verb)
                    if m:
                        _verb = m.group(0)
                if _verb:
                    ce = JapaneseConjugationEngine()
                    conj_result = ce.validate(_verb, _form, transcript_clean)
            except Exception:
                conj_result = None

        # 1. Deterministic pattern matching check
        pattern_found = False
        for pat in target_patterns:
            pat_str = str(pat).strip()
            if not pat_str:
                continue
            pat_no_punct = re.sub(r"[。！？、\s\!\?\,\.]+", "", pat_str)
            if pat_str in transcript_clean or (pat_no_punct and pat_no_punct in transcript_no_punct):
                pattern_found = True
                break
            # Try basic regex ignoring whitespace
            pattern_regex = re.escape(pat_str)
            if re.search(pattern_regex, transcript_clean):
                pattern_found = True
                break

        # 2b. Reflex conjugation deterministic override
        if conj_result is not None:
            # Conjugation engine is authoritative for reflex_conjugation
            if conj_result["is_correct"]:
                base_score = 92.0
                is_success = True
                target_usage = "correct"
                feedback = f"Chính xác! {conj_result['canonical']} ✓"
                evidence = [f"Động từ: {conj_result.get('verb_class')} {conj_result.get('form')}", f"Matched: {conj_result.get('matched')}"]
                grammar_score = 100.0
                naturalness_score = 95.0
                confidence = 0.92
            else:
                base_score = 28.0
                is_success = False
                target_usage = "incorrect"
                fb_extra = f" Đáp án: {conj_result['canonical']}"
                if conj_result.get("accepted"):
                    fb_extra += f" (cũng chấp nhận: {', '.join(conj_result['accepted'])})"
                feedback = f"Chưa chính xác.{fb_extra}"
                evidence = [f"User: {transcript_clean}", f"Expected: {conj_result['canonical']}", f"Accepted: {conj_result.get('accepted')}"]
                grammar_score = 30.0
                naturalness_score = 35.0
                confidence = 0.88
            # Apply reflex scoring policy for reaction dimension
            try:
                from app.domains.reflex.scoring import ReflexScoringPolicy
                _lat = _reflex.get("reaction_latency_ms", response_speed_ms)
                _timer = _reflex.get("timer_limit_ms")
                _conf = _reflex.get("speech_confidence")
                _indep = _reflex.get("independence") or ("assisted_hint" if used_hint else "independent")
                _policy = ReflexScoringPolicy.build(
                    "reflex_conjugation",
                    reaction_latency_ms=_lat,
                    timer_limit_ms=_timer,
                    speech_confidence=_conf,
                    accuracy_score=grammar_score,
                    naturalness_score=naturalness_score,
                    fluency_score=85.0 if is_success else 40.0,
                    timed_out=_timed_out,
                    late_response=_late,
                    independence_level=_indep,
                )
                base_score = _policy.overall.score
                # Enrich evidence with reaction
                if _lat is not None:
                    evidence.append(f"Reaction: {_lat:.0f}ms / {_timer}ms")
            except Exception:
                pass
            # Blend still respects timed_out
            final_score = max(0.0, min(100.0, round(base_score, 1)))
            return ExerciseResult(
                exercise_id=exercise.id,
                user_id=exercise.user_id,
                score=final_score,
                success=is_success,
                confidence=confidence,
                target_mastery_delta={},
                feedback=feedback,
                evidence=evidence,
                metrics={
                    "pattern_found": is_success,
                    "used_hint": used_hint,
                    "response_speed_ms": response_speed_ms,
                    "grammar_score": grammar_score,
                    "naturalness_score": naturalness_score,
                    "pronunciation_score": pronunciation_score,
                    "reflex": _reflex,
                    "conjugation": conj_result,
                },
                independence=IndependenceLevel.ASSISTED_HINT if used_hint else IndependenceLevel.INDEPENDENT,
                response_speed_ms=response_speed_ms,
                target_usage=target_usage,
                pronunciation_score=pronunciation_score,
                grammar_score=grammar_score,
                naturalness_score=naturalness_score,
                attempt_id=attempt.id,
            )

        # 3. AI Evaluation for qualitative naturalness and semantics
        # For reflex Q&A/context/transformation, tag task accordingly
        is_reflex = exercise.exercise_type.startswith("reflex")
        # Deterministic canonical check for transformation/context before AI (fast path)
        def _norm_jp(s: str) -> str:
            return re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", s.strip()) if s else ""
        _canonical_norm = None
        _canonical_raw = None
        if is_reflex and exercise.extra_metadata:
            try:
                _rc = exercise.extra_metadata.get("reflex_config", {}) or {}
                _canonical_raw = _rc.get("canonical") or _rc.get("expected")
                if _canonical_raw:
                    _canonical_norm = _norm_jp(str(_canonical_raw))
            except Exception:
                _canonical_norm = None
        # Also check acceptable_variants for exact match
        _accepted_norms = []
        if is_reflex and exercise.acceptable_variants:
            try:
                _accepted_norms = [_norm_jp(str(v)) for v in exercise.acceptable_variants]
            except Exception:
                _accepted_norms = []
        _deterministic_match = False
        if _canonical_norm and transcript_no_punct:
            if transcript_no_punct == _canonical_norm or transcript_no_punct in _canonical_norm or _canonical_norm in transcript_no_punct:
                _deterministic_match = True
            elif transcript_no_punct in _accepted_norms or _canonical_norm in _accepted_norms:
                _deterministic_match = True
            elif any(transcript_no_punct == av for av in _accepted_norms):
                _deterministic_match = True

        ai_eval = await self._evaluate_with_ai(
            user_id=exercise.user_id,
            exercise=exercise,
            user_transcript=transcript_clean,
            reflex_mode=is_reflex,
            reflex_context=_reflex,
        )
        # If deterministic canonical match, override AI pessimism
        if _deterministic_match and ai_eval:
            # Force high scores if transcript matches canonical exactly
            ai_eval["success"] = True
            ai_eval["score"] = max(float(ai_eval.get("score", 0)), 92.0)
            ai_eval["grammar_score"] = max(float(ai_eval.get("grammar_score", 0)), 95.0)
            ai_eval["naturalness_score"] = max(float(ai_eval.get("naturalness_score", 0)), 90.0)
            ai_eval["context_fit"] = max(float(ai_eval.get("context_fit", 70)), 90.0)
            ai_eval["completeness"] = max(float(ai_eval.get("completeness", 80)), 95.0)
            ai_eval["confidence"] = max(float(ai_eval.get("confidence", 0.85)), 0.9)
        elif _deterministic_match and not ai_eval:
            # No AI but deterministic match => fabricate success
            ai_eval = {
                "success": True,
                "score": 95.0,
                "grammar_score": 100.0,
                "naturalness_score": 90.0,
                "context_fit": 95.0,
                "completeness": 95.0,
                "confidence": 0.92,
                "feedback": f"Chính xác! Khớp đáp án mẫu: {_canonical_raw}",
                "evidence": [f"Exact match: {transcript_clean} == {_canonical_raw}"],
            }

        # 4. Synthesize overall score & metrics
        if ai_eval:
            try:
                base_score = float(ai_eval.get("score", 75.0))
            except Exception:
                base_score = 75.0
            # For reflex, respect AI success but also pattern/completeness gates
            is_reflex_qna = is_reflex and exercise.exercise_type in ("reflex_qna", "reflex_context", "reflex_transformation")
            if is_reflex_qna:
                try:
                    ctx_fit = float(ai_eval.get("context_fit", 70))
                except Exception:
                    ctx_fit = 70.0
                try:
                    completeness = float(ai_eval.get("completeness", 80))
                except Exception:
                    completeness = 80.0
                # Heuristic completeness gate (server-owned): single-word answers like 映画。 are incomplete per spec #19
                # Compute heuristic based on normalized transcript length
                try:
                    _norm_len = len(transcript_no_punct) if transcript_no_punct else len(transcript_clean)
                    if _norm_len <= 2 or transcript_clean.strip() in ("映画。", "映画", "はい。", "はい", "いいえ。", "いいえ"):
                        heuristic_comp = 30.0
                    elif _norm_len <= 4:
                        heuristic_comp = 55.0
                    else:
                        heuristic_comp = 85.0
                except Exception:
                    heuristic_comp = 85.0
                # Take minimum of AI and heuristic (heuristic is ground truth for completeness)
                completeness = min(completeness, heuristic_comp)
                # Also push corrected completeness back to ai_eval for scoring below
                ai_eval["completeness"] = completeness
                ai_eval["context_fit"] = ctx_fit
                # Incomplete or context mismatch => not success even if grammar ok
                if completeness < 50 or ctx_fit < 40:
                    is_success = False
                else:
                    is_success = bool(ai_eval.get("success", True))
                # Force fail if heuristic says too short, even if AI says success
                if heuristic_comp < 50:
                    is_success = False
            else:
                is_success = bool(ai_eval.get("success", True)) and (pattern_found or base_score >= 80)
            try:
                confidence = float(ai_eval.get("confidence", 0.85))
                confidence = max(0.0, min(1.0, confidence))
            except Exception:
                confidence = 0.85
            feedback = ai_eval.get("feedback", "Bạn đã hoàn thành bài tập khá tốt!")
            evidence = ai_eval.get("evidence", [])
            if isinstance(evidence, str):
                evidence = [evidence]
            elif not isinstance(evidence, list):
                evidence = [str(evidence)]
            target_usage = ai_eval.get("target_usage", "correct" if pattern_found else "partial")
            try:
                grammar_score = float(ai_eval.get("grammar_score", base_score))
            except Exception:
                grammar_score = base_score
            try:
                naturalness_score = float(ai_eval.get("naturalness_score", base_score))
            except Exception:
                naturalness_score = base_score
            # For reflex, also capture context_fit/completeness
            if is_reflex:
                # Will be used in scoring policy below
                pass
        else:
            # Fallback deterministic evaluation
            if pattern_found:
                base_score = 85.0
                is_success = True
                target_usage = "correct"
                feedback = "Bạn đã sử dụng thành công mẫu câu/từ vựng mục tiêu trong bài tập!"
                evidence = [f"Phát hiện cấu trúc mục tiêu trong câu: {transcript_clean}"]
            else:
                base_score = 55.0
                is_success = False
                target_usage = "not_attempted"
                feedback = "Chưa phát hiện rõ cấu trúc mục tiêu trong câu nói. Hãy thử lại để củng cố phản xạ nhé."
                evidence = [f"Câu nói: {transcript_clean}"]

            confidence = 0.70
            grammar_score = turn_analysis_score or base_score
            naturalness_score = base_score

        # Apply reflex scoring policy if reflex exercise (overrides simple blend)
        if is_reflex and exercise.exercise_type != "reflex_conjugation":
            try:
                from app.domains.reflex.scoring import ReflexScoringPolicy
                _lat = _reflex.get("reaction_latency_ms", response_speed_ms)
                _timer = _reflex.get("timer_limit_ms")
                _conf = _reflex.get("speech_confidence")
                _indep = _reflex.get("independence") or ("assisted_hint" if used_hint else "independent")
                # Extract AI context_fit/completeness if available
                try:
                    _ctx = float(ai_eval.get("context_fit", grammar_score)) if ai_eval else grammar_score
                except Exception:
                    _ctx = grammar_score
                # Completeness: heuristic minimum vs AI
                try:
                    _norm_len2 = len(transcript_no_punct) if transcript_no_punct else len(transcript_clean)
                    if _norm_len2 <= 2 or transcript_clean.strip() in ("映画。", "映画", "はい。", "はい", "いいえ。", "いいえ"):
                        _heur2 = 30.0
                    elif _norm_len2 <= 4:
                        _heur2 = 55.0
                    else:
                        _heur2 = 85.0
                except Exception:
                    _heur2 = 85.0
                try:
                    _ai_comp = float(ai_eval.get("completeness", _heur2)) if ai_eval else _heur2
                    _comp = min(_ai_comp, _heur2)
                except Exception:
                    _comp = _heur2
                try:
                    _nat = float(ai_eval.get("naturalness_score", naturalness_score)) if ai_eval else naturalness_score
                except Exception:
                    _nat = naturalness_score
                _policy = ReflexScoringPolicy.build(
                    exercise.exercise_type,
                    reaction_latency_ms=_lat,
                    timer_limit_ms=_timer,
                    speech_confidence=_conf,
                    accuracy_score=grammar_score,
                    naturalness_score=_nat,
                    fluency_score=75.0,
                    context_fit_score=_ctx,
                    completeness_score=_comp,
                    timed_out=_timed_out,
                    late_response=_late,
                    independence_level=_indep,
                )
                final_score = _policy.overall.score
                # Cap score for incomplete responses (spec #19): "映画。" must not get high score
                if _comp < 50:
                    final_score = min(final_score, 55.0)
                if _ctx < 40:
                    final_score = min(final_score, 55.0)
                # Enrich evidence
                evidence = evidence + [_policy.overall.evidence[0]] if evidence else [_policy.overall.evidence[0]]
            except Exception:
                # Fallback to blend
                if turn_analysis_score is not None:
                    base_score = (base_score * 0.60) + (turn_analysis_score * 0.40)
                if pronunciation_score is not None:
                    base_score = (base_score * 0.70) + (pronunciation_score * 0.30)
                final_score = max(0.0, min(100.0, round(base_score, 1)))
        else:
            # Blend with turn analysis score or pronunciation score if present
            if turn_analysis_score is not None:
                base_score = (base_score * 0.60) + (turn_analysis_score * 0.40)
            if pronunciation_score is not None:
                base_score = (base_score * 0.70) + (pronunciation_score * 0.30)
            final_score = max(0.0, min(100.0, round(base_score, 1)))

        # Merge reflex metrics into result metrics
        _metrics = {
            "pattern_found": pattern_found,
            "used_hint": used_hint,
            "response_speed_ms": response_speed_ms,
            "grammar_score": grammar_score,
            "naturalness_score": naturalness_score,
            "pronunciation_score": pronunciation_score,
        }
        if _reflex:
            _metrics["reflex"] = _reflex
            # Also flatten for convenience
            if _reflex.get("reaction_latency_ms") is not None:
                _metrics["reaction_latency_ms"] = _reflex.get("reaction_latency_ms")
            if _reflex.get("timer_limit_ms") is not None:
                _metrics["timer_limit_ms"] = _reflex.get("timer_limit_ms")
            _metrics["timed_out"] = _timed_out
            _metrics["late_response"] = _late

        return ExerciseResult(
            exercise_id=exercise.id,
            user_id=exercise.user_id,
            score=final_score,
            success=is_success,
            confidence=confidence,
            target_mastery_delta={},  # Computed by LearningItemService
            feedback=feedback,
            evidence=evidence,
            metrics=_metrics,
            independence=indep,
            response_speed_ms=response_speed_ms,
            target_usage=target_usage,
            pronunciation_score=pronunciation_score,
            grammar_score=grammar_score,
            naturalness_score=naturalness_score,
            attempt_id=attempt.id,
        )

    async def _evaluate_with_ai(
        self,
        user_id: str,
        exercise: Exercise,
        user_transcript: str,
        reflex_mode: bool = False,
        reflex_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Invokes AIRouter with structured output schema for exercise evaluation."""
        if not user_transcript:
            return None

        if reflex_mode:
            # Reflex evaluation uses dedicated prompt with extra reflex context
            sys_inst, user_content = LearningPrompts.build_reflex_evaluation_prompt(
                sub_mode=exercise.exercise_type,
                prompt=exercise.scenario or exercise.title,
                user_transcript=user_transcript,
                expected=(exercise.target_patterns[0] if exercise.target_patterns else None),
                semantic_target=(exercise.extra_metadata or {}).get("reflex_config") if exercise.extra_metadata else None,
                reaction_latency_ms=(reflex_context or {}).get("reaction_latency_ms"),
                timer_limit_ms=(reflex_context or {}).get("timer_limit_ms"),
            )
            task = AITask.REFLEX_EVALUATION
        else:
            sys_inst, user_content = LearningPrompts.build_exercise_evaluation_prompt(
                exercise_title=exercise.title,
                exercise_objective=exercise.objective,
                target_patterns=exercise.target_patterns or [],
                user_transcript=user_transcript,
                context_notes=exercise.scenario,
            )
            task = AITask.EXERCISE_EVALUATION

        req = AIRequest(
            task=task,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.2,
            max_output_tokens=600 if reflex_mode else 500,
            user_id=user_id,
        )

        try:
            resp = await self.ai_router.generate(task=task, request=req, user_id=user_id)
            clean_text = resp.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text.replace("```json", "", 1).rstrip("```").strip()
            elif clean_text.startswith("```"):
                clean_text = clean_text.replace("```", "", 1).rstrip("```").strip()

            parsed = json.loads(clean_text)
            # Sanitize AI output (defensive: LLM may return confidence 5.0 or evidence as string)
            try:
                if "confidence" in parsed:
                    c = float(parsed["confidence"])
                    # If model returns 5 instead of 0.5, normalize: clamp 0-1, or divide by 10 if >1
                    if c > 1.0:
                        if c <= 10:
                            c = c / 10.0 if c > 5 else min(1.0, c / 5.0)
                        else:
                            c = 1.0
                    parsed["confidence"] = max(0.0, min(1.0, c))
                if "evidence" in parsed and isinstance(parsed["evidence"], str):
                    parsed["evidence"] = [parsed["evidence"]]
                if "score" in parsed:
                    parsed["score"] = max(0.0, min(100.0, float(parsed["score"])))
                for k in ("grammar_score", "naturalness_score", "context_fit", "completeness"):
                    if k in parsed and parsed[k] is not None:
                        try:
                            parsed[k] = max(0.0, min(100.0, float(parsed[k])))
                        except Exception:
                            pass
            except Exception:
                pass
            return parsed
        except Exception as e:
            logger.warning(f"[ExerciseEvaluator] AI evaluation error: {e}")
            return None
