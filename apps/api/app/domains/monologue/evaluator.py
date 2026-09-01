"""MonologueEvaluator — combines deterministic pipeline + AI semantic + scoring (§15-39)."""

from __future__ import annotations

import base64
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.monologue.ai.analyzer import MonologueAIAnalyzer
from app.domains.monologue.analytics.pipeline import MonologuePipeline
from app.domains.monologue.contracts import SpeechGenre
from app.domains.monologue.scoring.speech_scoring import SpeechScoringPolicy
from app.domains.speech.stt_router import stt_router
from app.domains.speech.contracts import STTOptions


class MonologueEvaluator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipeline = MonologuePipeline()
        self.ai = MonologueAIAnalyzer(db)

    async def evaluate(
        self,
        exercise: Any,
        user_transcript: str | None,
        audio_base64: str | None,
        speech_metrics: dict[str, Any] | None,
        target_duration_ms: int,
        user_id: str,
    ) -> dict[str, Any]:
        # 1. Resolve transcript via STT if audio provided (authoritative) or text-only (office/broken mic)
        transcript = (user_transcript or "").strip()
        words: list[dict] = []
        stt_conf = None
        duration_ms = None
        has_clipping = False
        snr_db = None
        is_text_only = False

        audio_bytes: bytes | None = None
        if audio_base64:
            # Strip data: prefix and whitespace, validate before decode (DoS guard)
            import re
            b64_clean = audio_base64.strip()
            if "," in b64_clean and b64_clean.startswith("data:"):
                b64_clean = b64_clean.split(",", 1)[1]
            b64_clean = re.sub(r"\s", "", b64_clean)
            # approx before decode (account padding)
            approx_bytes = len(b64_clean) * 3 // 4 - b64_clean.count("=")
            if approx_bytes > 10 * 1024 * 1024:
                raise ValueError("Audio too large (>10MB) — please use shorter duration")
            if len(b64_clean) > 14_000_000:
                raise ValueError("Audio too large (>10MB) — please use shorter duration")
            try:
                audio_bytes = base64.b64decode(b64_clean, validate=True)
            except Exception as e:
                logger.warning(f"[MonologueEvaluator] Invalid base64 audio: {e}")
                raise ValueError("Invalid audio data: base64 decode failed") from e
            if len(audio_bytes) > 10 * 1024 * 1024:
                raise ValueError("Audio too large (>10MB) — please use shorter duration")
            # quick quality check
            try:
                from app.domains.audio.recording_service import AudioQualityAnalyzer

                qr = AudioQualityAnalyzer.analyze(audio_bytes)
                has_clipping = bool(getattr(qr, "has_clipping", False))
                snr_db = getattr(qr, "snr_db", None)
                duration_ms = getattr(qr, "duration_ms", None)
            except Exception as e:
                logger.debug(f"[MonologueEvaluator] AudioQualityAnalyzer failed: {e}", exc_info=True)
            try:
                stt_res = await stt_router.transcribe(audio_bytes=audio_bytes, options=STTOptions(language="ja", model="base"))
                transcript = stt_res.text.strip() or transcript
                words = [{"word": w.word, "start_ms": w.start_ms, "end_ms": w.end_ms, "confidence": w.confidence, "pos": getattr(w, "pos", None)} for w in (stt_res.words or [])]
                stt_conf = stt_res.confidence
                if stt_res.duration_ms:
                    duration_ms = stt_res.duration_ms
            except Exception as e:
                logger.warning(f"[MonologueEvaluator] STT failed: {e}", exc_info=True)
                raise ValueError("Speech recognition failed — please retry with clearer audio") from e
        else:
            # Text-only submission (Office mode / Broken mic)
            if not transcript:
                return {
                    "status": "RETRY_AUDIO",
                    "score": 0.0,
                    "success": False,
                    "confidence": 0.3,
                    "feedback": "Vui lòng nhập văn bản bài nói tiếng Nhật của bạn hoặc thu âm qua micro.",
                    "evidence": ["No transcript and no audio provided"],
                    "assessment": {"overall": 0, "fluency": 0, "coherence": 0, "grammar": None, "vocabulary": None, "naturalness": None, "relevance": None, "discourse": 0, "pronunciation": None},
                    "metrics": {"speech_duration_ms": 0, "target_duration_ms": target_duration_ms, "transcript": "", "word_count": 0, "quality_gate": {"status": "RETRY_AUDIO", "reason": "empty"}},
                    "is_low_confidence": True,
                }
            is_text_only = True
            stt_conf = 1.0
            if speech_metrics and speech_metrics.get("speech_duration_ms"):
                duration_ms = int(speech_metrics["speech_duration_ms"])
            else:
                # Estimate duration based on Japanese reading pace ~5.0 mora/sec
                duration_ms = max(5000, int((len(transcript) / 5.0) * 1000))

        # 2. Duration fallback — strictly server-derived
        if duration_ms is None:
            if words:
                try:
                    duration_ms = max(w["end_ms"] for w in words if w.get("end_ms"))  # type: ignore
                except Exception as e:
                    logger.debug(f"[MonologueEvaluator] duration from words failed: {e}")
                    duration_ms = None
            if duration_ms is None:
                if is_text_only:
                    duration_ms = max(5000, int((len(transcript) / 5.0) * 1000))
                else:
                    return {
                        "status": "RETRY_AUDIO",
                        "score": 0.0,
                        "success": False,
                        "confidence": 0.3,
                        "feedback": "Không xác định được thời lượng nói — vui lòng thu lại.",
                        "evidence": ["Missing duration and transcript timing"],
                        "assessment": {"overall": 0, "fluency": 0, "coherence": 0, "grammar": None, "vocabulary": None, "naturalness": None, "relevance": None, "discourse": 0, "pronunciation": None},
                        "metrics": {"speech_duration_ms": 0, "target_duration_ms": target_duration_ms, "transcript": transcript, "word_count": len(words), "quality_gate": {"status": "RETRY_AUDIO", "reason": "no duration"}},
                        "is_low_confidence": True,
                    }

        if not transcript:
            return {
                "status": "RETRY_AUDIO",
                "score": 0.0,
                "success": False,
                "confidence": 0.3,
                "feedback": "Không nhận diện được giọng nói. Vui lòng kiểm tra micro và nói to rõ hơn.",
                "evidence": ["STT returned empty transcript"],
                "assessment": {
                    "overall": 0,
                    "fluency": 0, "coherence": 0, "grammar": None, "vocabulary": None,
                    "naturalness": None, "relevance": None, "discourse": None, "pronunciation": None,
                },
                "metrics": {
                    "speech_duration_ms": duration_ms,
                    "target_duration_ms": target_duration_ms,
                    "transcript": transcript,
                    "word_count": len(words),
                    "quality_gate": {"status": "RETRY_AUDIO", "reason": "empty transcript"},
                },
                "is_low_confidence": True,
            }

        # 3. Deterministic pipeline — decode once, reuse
        genre_val = "opinion"
        topic = ""
        instruction = ""
        constraints: list[str] = []
        if exercise and hasattr(exercise, "extra_metadata") and exercise.extra_metadata:
            sc = exercise.extra_metadata.get("speech_config", {})
            genre_val = sc.get("genre") or exercise.extra_metadata.get("genre") or genre_val
            topic = sc.get("topic") or getattr(exercise, "title", "") or ""
            instruction = sc.get("instruction") or getattr(exercise, "instructions", "") or ""
            constraints = sc.get("constraints", []) or []
        try:
            det = await self.pipeline.analyze_transcript(
                transcript=transcript,
                words=words,
                speech_duration_ms=int(duration_ms),
                target_duration_ms=int(target_duration_ms),
                stt_confidence=stt_conf,
                audio_bytes=audio_bytes,
                genre=genre_val,
                has_clipping=has_clipping,
                snr_db=snr_db,
                is_text_only=is_text_only,
            )
        except Exception as e:
            logger.warning(f"[MonologueEvaluator] pipeline failed: {e}", exc_info=True)
            raise ValueError("Speech analysis pipeline failed") from e

        # 4. Quality gate check — don't assign false low fluency, but surface error visibly
        qg = det.get("quality_gate", {})
        is_low = qg.get("status") in ("LOW_CONFIDENCE", "RETRY_AUDIO")
        if not is_text_only and qg.get("status") == "RETRY_AUDIO":
            # Hard fail — surface to UI via toast (no silent downgrade)
            return {
                "status": "RETRY_AUDIO",
                "score": 0.0,
                "success": False,
                "confidence": 0.3,
                "feedback": "Chất lượng audio chưa đủ để chấm chính xác. Vui lòng thu lại ở nơi yên tĩnh hơn.",
                "evidence": [qg.get("reason", "Audio unreliable")],
                "metrics": det,
                "is_low_confidence": True,
            }

        # 5. AI semantic — block on LOW_CONFIDENCE, require sufficient text
        ai_res = None
        ai_error: str | None = None
        if not is_low and det["speech_metrics_core"]["total_chars"] > 50:
            try:
                det_ctx = {
                    "speech_duration_ms": duration_ms,
                    "target_duration_ms": target_duration_ms,
                    "pause_count": det["pause_summary"]["total"],
                    "filler_count": det["filler_summary"]["filler_count"],
                    "mora_per_sec": det["speech_metrics_core"].get("mora_per_sec"),
                    "chars_per_min": det["speech_metrics_core"]["chars_per_min"],
                    "idea_density": det["idea_density"],
                    "lexical_ttr": det["lexical_profile"]["type_token_ratio"],
                    "discourse_missing": det["discourse"]["missing_elements"],
                    "coherence_deterministic": det["coherence_deterministic"],
                }
                ai_res = await self.ai.evaluate(
                    user_id=user_id,
                    genre=genre_val,
                    topic=topic,
                    instruction=instruction,
                    constraints=constraints,
                    transcript=transcript,
                    deterministic=det_ctx,
                    duration_sec=int(target_duration_ms / 1000),
                )
            except Exception as e:
                ai_error = str(e)
                logger.warning(f"[MonologueEvaluator] AI eval error: {e}", exc_info=True)

        # 6. Native upgrade (separate, non-blocking for scoring)
        upgrade = None
        try:
            if transcript and len(transcript) > 10 and not is_low:
                upgrade = await self.ai.native_upgrade(user_id=user_id, transcript=transcript, genre=genre_val, topic=topic, level="N3")
        except Exception as e:
            logger.warning(f"[MonologueEvaluator] upgrade error: {e}", exc_info=True)

        # 7. Scoring — no hard-coded mock scores (hard fail per user choice: remove 78 etc.)
        fluency = SpeechScoringPolicy.compute_fluency_score(
            pause_summary=det["pause_summary"],
            filler_summary=det["filler_summary"],
            rate_quality=det.get("rate_quality", "normal"),
            self_repair_summary=det["repair_summary"],
            duration_ms=int(duration_ms),
            target_ms=int(target_duration_ms),
        )
        coh_det = det["coherence_deterministic"]["overall"]

        # Vocabulary: if lexical profile missing, return None (no mock)
        lex = det["lexical_profile"]
        vocab_score: float | None = None
        if lex is not None and lex.get("mattr") is not None:
            # per-level calibration placeholder — still deterministic but without mock constant fallback
            mattr = float(lex.get("mattr", 0))
            if mattr > 0:
                # map mattr 0.3..0.9 -> 55..90
                vocab_score = round(max(45, min(92, 55 + (mattr - 0.3) * 58)), 1)

        # AI-derived scores — None if AI unavailable (hard fail: no mock)
        ai_coh = ai_res.get("coherence") if ai_res else None
        ai_nat = ai_res.get("naturalness") if ai_res else None
        ai_rel = ai_res.get("relevance") if ai_res else None
        ai_genre = ai_res.get("genre_fit") if ai_res else None
        grammar_score: float | None = None
        if ai_res and ai_res.get("grammar") is not None:
            try:
                grammar_score = float(ai_res.get("grammar"))
            except Exception:
                grammar_score = None
        elif ai_res:
            # try explicit grammar field, else derive from AI only if present — no mock 78
            grammar_score = None

        # discourse derived from connector quality
        disc_map = {"appropriate": 85, "present": 70, "repeated": 60, "missing": 45}
        disc_score: float | None = disc_map.get(det["discourse"]["connector_quality"])

        genre_e = genre_val
        try:
            genre_e = SpeechGenre(genre_val.lower()) if isinstance(genre_val, str) else genre_val
        except ValueError:
            genre_e = SpeechGenre.OPINION
            logger.debug(f"[MonologueEvaluator] unknown genre {genre_val}, fallback to OPINION")

        overall, weights = SpeechScoringPolicy.compute_overall(
            fluency=fluency,
            coherence_det=coh_det,
            coherence_ai=ai_coh,
            grammar=grammar_score,
            vocab=vocab_score,
            naturalness_ai=ai_nat,
            relevance_ai=ai_rel,
            discourse=disc_score,
            pronunciation=None,
            genre=genre_e,
        )

        success = overall >= 60 and not is_low and qg.get("status") == "ok"
        # conclusion penalty only if expected structure ends with conclusion/summary
        from app.domains.monologue.generation.genre_ontology import GENRE_STRUCTURE
        try:
            expected = GENRE_STRUCTURE.get(genre_e, [])
            expected_last = expected[-1] if expected else "conclusion"
            if expected_last in det["discourse"]["missing_elements"] and int(target_duration_ms / 1000) >= 60:
                success = success and overall >= 65
        except Exception:
            if "conclusion" in det["discourse"]["missing_elements"] and int(target_duration_ms / 1000) >= 60:
                success = success and overall >= 65

        feedback = "Bài nói khá tốt, tiếp tục phát huy!"
        evidence: list[str] = []
        main_weak = None
        main_strength = None
        if ai_res:
            feedback = ai_res.get("feedback", [""])[0] if isinstance(ai_res.get("feedback"), list) and ai_res["feedback"] else ai_res.get("main_weakness") or feedback
            if isinstance(ai_res.get("feedback"), list):
                evidence = ai_res["feedback"]
            main_weak = ai_res.get("main_weakness")
            main_strength = ai_res.get("main_strength")
        else:
            # deterministic only — surface AI unavailable explicitly (no mock)
            if ai_error:
                evidence = [f"AI unavailable ({ai_error}) — deterministic only", f"Fluency {fluency}, Coherence {coh_det}, Filler {det['filler_summary']['filler_count']}/min {det['filler_summary']['filler_per_min']}"]
                feedback = f"AI đánh giá tạm thời không khả dụng — kết quả dựa trên phân tích định lượng. {('Cần bổ sung: ' + ', '.join(det['discourse']['missing_elements']) + '.') if det['discourse']['missing_elements'] else ''}"
            else:
                if det["discourse"]["missing_elements"]:
                    feedback = f"Cần bổ sung: {', '.join(det['discourse']['missing_elements'])}."
                if det["filler_summary"]["filler_count"] > 6:
                    feedback += " Giảm filler (えーと/あのー) để trôi chảy hơn."
                evidence = [f"Fluency {fluency}, Coherence {coh_det}, Filler {det['filler_summary']['filler_count']}/min {det['filler_summary']['filler_per_min']}"]
            if is_low:
                evidence.append(f"Quality gate: {qg.get('status')} — {qg.get('reason')}")

        # Build assessment — no mocks, missing signals are None (renormalized in scoring)
        ai_conf = ai_res.get("confidence", 0.6) if ai_res else 0.55
        if ai_error:
            ai_conf = 0.5
        assessment = {
            "overall": overall,
            "fluency": fluency,
            "coherence": coh_det if ai_coh is None else round(coh_det * 0.45 + ai_coh * 0.55, 1),
            "grammar": grammar_score,
            "vocabulary": vocab_score,
            "naturalness": ai_nat,
            "relevance": ai_rel,
            "discourse": disc_score,
            "pronunciation": None,
            "content": ai_res.get("content_score") if ai_res and ai_res.get("content_score") is not None else idea_score_from_det(det["idea_density"]),
            "confidence": ai_conf,
            "weights": weights,
            "genre_fit": ai_genre,
            "main_strength": main_strength,
            "main_weakness": main_weak,
            "ai_error": ai_error,
        }

        # Upgrade explanations (compare minimal vs native)
        upgrade_explanations = []
        if upgrade and upgrade.get("explanations"):
            upgrade_explanations = upgrade["explanations"]

        result = {
            "status": "completed",
            "score": overall,
            "success": success,
            "confidence": assessment["confidence"],
            "feedback": feedback if isinstance(feedback, str) else " ".join(feedback) if isinstance(feedback, list) else str(feedback),
            "evidence": evidence,
            "assessment": assessment,
            "metrics": {
                **det,
                "transcript": transcript,
                "word_count": len(words),
                "words": words,
            },
            "upgrade": upgrade,
            "upgrade_explanations": upgrade_explanations,
            "is_low_confidence": is_low,
            "ai_result": ai_res,
        }
        return result


def idea_score_from_det(idea: dict) -> float:
    # map idea density to 0-100
    uniq = idea.get("unique_ideas", 0)
    repeated = idea.get("repeated_ideas", 0)
    examples = idea.get("examples", 0)
    base = min(90, 60 + uniq * 8 + examples * 5 - repeated * 7)
    return max(35, base)
