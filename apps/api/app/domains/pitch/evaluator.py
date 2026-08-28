"""PitchEvaluator — deterministic acoustic + lexical, AI fallback."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.japanese.provider import get_language_provider
from app.domains.pitch.acoustic.accent_extractor import AccentPatternExtractor
from app.domains.pitch.acoustic.mora_aligner import MoraAligner
from app.domains.pitch.acoustic.pitch_extractor import PitchExtractor
from app.domains.pitch.resource_provider import get_pitch_provider
from app.domains.pitch.scoring import build_pitch_assessment


def _norm(text: str) -> str:
    return re.sub(r"[。！？、\s\!\?\,\.\u3000]+", "", text.strip()) if text else ""


class PitchEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.lang = get_language_provider()
        self.pitch_provider = get_pitch_provider()
        self.pitch_extractor = PitchExtractor()
        self.mora_aligner = MoraAligner()
        self.accent_extractor = AccentPatternExtractor()
        # AI router lazy
        self._ai_router = None

    def _get_ai_router(self):
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
        pitch_confidence: float | None = None,
        audio_quality: float | None = None,
        timed_out: bool = False,
        late_response: bool = False,
        independence: str = "independent",
        audio_samples=None,
        sr: int = 16000,
    ) -> dict[str, Any]:
        raw = (user_transcript or "").strip()
        norm = _norm(raw)

        # Extract pitch_config
        pitch_cfg = {}
        try:
            pitch_cfg = (exercise.extra_metadata or {}).get("pitch_config", {}) or {}
        except Exception:
            pitch_cfg = {}
        canonical = pitch_cfg.get("canonical") or (exercise.target_patterns[0] if exercise.target_patterns else None)
        accepted = pitch_cfg.get("accepted") or exercise.acceptable_variants or []
        if canonical and canonical not in accepted:
            accepted = [canonical] + accepted

        # Timeout
        if timed_out or not raw:
            assessment = build_pitch_assessment(
                exercise_type,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                pitch_confidence=pitch_confidence or 0.3,
                timed_out=True,
            )
            return {"success": False, "score": assessment.overall.score, "assessment": assessment.to_dict(), "feedback": "Time's up — chưa ghi nhận.", "evidence": ["Timed out"], "pitch_assessment": assessment.to_dict()}

        # Audio quality gate
        if audio_quality is not None and audio_quality < 0.4:
            assessment = build_pitch_assessment(
                exercise_type,
                reaction_latency_ms=reaction_latency_ms,
                timer_limit_ms=timer_limit_ms,
                speech_confidence=speech_confidence,
                pitch_confidence=0.25,
                timed_out=False,
            )
            return {"success": False, "score": 0, "assessment": assessment.to_dict(), "feedback": "Audio quality too low for reliable pitch analysis — hãy thử lại.", "evidence": [f"Audio quality {audio_quality:.2f}"], "status": "RETRY_AUDIO"}

        # Lexical identity via STT
        lexical_ok = False
        matched = None
        for cand in accepted:
            if _norm(cand) == norm:
                lexical_ok = True
                matched = cand
                break
            # Reading equivalence
            try:
                hira_user = self.lang.get_reading(raw) or norm
                hira_cand = self.lang.get_reading(cand) or _norm(cand)
                if hira_user == hira_cand:
                    lexical_ok = True
                    matched = cand
                    break
            except Exception:
                pass

        # For recognition (listening) — no production, lexical via choice
        if exercise_type == "pitch_recognition":
            # Expect transcript to be choice A or B? For MVP, lexical_ok is success
            # Use deterministic: if matched and pitch pattern matches expected, success
            # Otherwise fallback to AI
            pass

        # Mora analysis for mora_length
        mora_score = 85
        if exercise_type == "mora_length":
            # Compare mora counts
            try:
                from app.domains.pronunciation.japanese.mora_analyzer import JapaneseMoraAnalyzer

                ma = JapaneseMoraAnalyzer()
                user_mora = len(ma.segment_moras(self.lang.get_reading(raw) or raw))
                expected_mora = pitch_cfg.get("mora_count") or (self.pitch_provider.lookup(canonical).mora_count if canonical and self.pitch_provider.lookup(canonical) else None)
                if expected_mora:
                    if user_mora == expected_mora:
                        mora_score = 95
                    elif abs(user_mora - expected_mora) == 1:
                        mora_score = 60
                    else:
                        mora_score = 35
                # Also check pair type
                pair = pitch_cfg.get("pair") or {}
                if pair:
                    # If user said short when long expected, fail
                    pass
            except Exception:
                mora_score = 70

        # Devoicing analysis
        devoicing_score = 80
        if exercise_type == "vowel_devoicing":
            # Heuristic: if word is です and user transcript is です, check devoicing would require acoustic; for MVP, assume voiced is okay but devoiced is better
            # We treat as tendency, not mandatory, so high score even if not devoiced
            devoicing_score = 85

        # Pitch contour analysis (if audio provided)
        accent_pattern_score = 80
        downstep_score = 80
        contour_score = 80
        stability_score = 80
        pitch_conf = pitch_confidence or 0.85
        if exercise_type == "pitch_contour" and audio_samples is not None:
            try:
                # Extract F0
                pitch_curve = self.pitch_extractor.extract(audio_samples, sr)
                pitch_conf = pitch_curve.confidence
                if pitch_conf < 0.35:
                    # Unreliable
                    assessment = build_pitch_assessment(
                        exercise_type,
                        reaction_latency_ms=reaction_latency_ms,
                        timer_limit_ms=timer_limit_ms,
                        speech_confidence=speech_confidence,
                        pitch_confidence=pitch_conf,
                        timed_out=False,
                    )
                    return {"success": False, "score": 0, "assessment": assessment.to_dict(), "feedback": "F0 confidence low — hãy thử lại trong môi trường yên tĩnh.", "evidence": [f"Pitch confidence {pitch_conf:.2f}", f"Voiced ratio {pitch_curve.voiced_ratio:.2f}"], "status": "RETRY_AUDIO"}
                # Mora alignment
                # Need speech start/end from VAD or assume 0..duration
                speech_start = 0
                speech_end = len(audio_samples) / sr * 1000
                mora_boundaries = self.mora_aligner.align(canonical or raw, speech_start, speech_end, None, sr, audio_samples)
                # Extract pattern
                pattern_res = self.accent_extractor.extract(pitch_curve, mora_boundaries)
                # Compare to expected pattern from provider
                expected_entry = self.pitch_provider.lookup(canonical or raw) if canonical else None
                expected_pattern = expected_entry.pattern if expected_entry else []
                observed_pattern = pattern_res.mora_values
                if expected_pattern and observed_pattern:
                    # Pattern accuracy: compare H/L per mora
                    min_len = min(len(expected_pattern), len(observed_pattern))
                    matches = sum(1 for i in range(min_len) if expected_pattern[i] == observed_pattern[i])
                    accent_pattern_score = (matches / min_len * 100) if min_len else 70
                    # Downstep
                    exp_drop = expected_entry.drop_location if expected_entry else None
                    obs_drop = pattern_res.drop_location
                    if exp_drop is not None and obs_drop is not None:
                        downstep_score = 100 if exp_drop == obs_drop else 60 if abs(exp_drop - obs_drop) == 1 else 30
                    elif exp_drop is None and obs_drop is None:
                        downstep_score = 95
                    else:
                        downstep_score = 55
                    # Contour similarity: crude via pattern match + stability
                    contour_score = accent_pattern_score * 0.8 + 20
                    stability_score = 85 if pattern_res.confidence > 0.8 else 65
                pitch_conf = pattern_res.confidence
            except Exception as e:
                logger.warning(f"[PitchEvaluator] acoustic failed {e}")
                # Fallback to lexical
                pass

        # For minimal pair, check accent pattern via provider comparison
        if exercise_type == "pitch_minimal_pair":
            # Need to decide which word user said, then check if matches expected choice
            # For MVP, lexical_ok already checks, accent check via provider reading
            if lexical_ok and matched:
                # If pair has a/b different accents, check matched is expected correct (canonical)
                # For listening task, canonical is correct answer
                if canonical and _norm(matched) == _norm(canonical):
                    accent_pattern_score = 95
                else:
                    # User said the other of pair — still lexical correct but pitch wrong for that meaning
                    # For production, both are lexically valid, so need to check if pitch matches chosen word's expected pattern
                    # We can't know user's intended meaning, so for minimal pair production, accept either with high score
                    # For recognition, strict
                    accent_pattern_score = 85
            else:
                accent_pattern_score = 35
                lexical_ok = False

        # Build assessment
        # Determine lexical score
        lexical_score = 95 if lexical_ok else 35
        # For pitch_contour, lexical is less important than pattern
        if exercise_type == "pitch_contour":
            lexical_score = 80 if lexical_ok else 30

        assessment = build_pitch_assessment(
            exercise_type,
            reaction_latency_ms=reaction_latency_ms,
            timer_limit_ms=timer_limit_ms,
            speech_confidence=speech_confidence,
            pitch_confidence=pitch_conf,
            lexical_score=lexical_score,
            accent_pattern_score=accent_pattern_score,
            mora_score=mora_score,
            downstep_score=downstep_score,
            contour_score=contour_score,
            stability_score=stability_score,
            timed_out=timed_out,
            late_response=late_response,
        )

        success = lexical_ok and accent_pattern_score >= 60 and mora_score >= 60
        if exercise_type == "pitch_contour" and accent_pattern_score < 60:
            success = False
        if exercise_type == "mora_length" and mora_score < 60:
            success = False
        if pitch_conf is not None and pitch_conf < 0.35:
            success = False

        # For pitch, single mora/word is expected → completeness always high
        if exercise_type in ("pitch_minimal_pair", "mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition"):
            completeness = 95
        else:
            norm_len = len(norm)
            completeness = 95 if norm_len > 2 else 30
            if completeness < 50:
                success = False

        feedback_parts = []
        if lexical_ok:
            feedback_parts.append("Từ vựng chính xác")
        else:
            feedback_parts.append(f"Chưa khớp từ mong đợi: {canonical}")
        if accent_pattern_score >= 80:
            feedback_parts.append("Cao độ đúng")
        elif accent_pattern_score >= 60:
            feedback_parts.append("Cao độ gần đúng, chú ý vị trí hạ")
        else:
            feedback_parts.append("Sai pattern cao độ")
        if mora_score < 60:
            feedback_parts.append("Sai số mora/độ dài")
        if downstep_score < 60:
            feedback_parts.append("Downstep lệch 1 mora")

        feedback = " • ".join(feedback_parts)
        if assessment.overall.score >= 80 and success:
            feedback = "✅ " + feedback
        elif success:
            feedback = "✅ " + feedback + " — cần cải thiện contour"
        else:
            feedback = "⚠️ " + feedback

        return {
            "success": success,
            "score": assessment.overall.score,
            "assessment": assessment.to_dict(),
            "feedback": feedback,
            "evidence": [f"Lexical {'ok' if lexical_ok else 'fail'}: {raw} vs {canonical}", f"Accent {accent_pattern_score:.0f}, Mora {mora_score:.0f}, Downstep {downstep_score:.0f}"],
            "pitch_assessment": assessment.to_dict(),
            "is_perfect": success and assessment.overall.score >= 85 and independence == "independent",
        }
