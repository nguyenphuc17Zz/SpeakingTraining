"""RampEvaluator — evaluates a Mode 6 exercise attempt.

§28 Grammar Evaluation, §29 Lexical Difficulty, §33 Automaticity,
§34 RampScore, §35 Stage-specific scoring, §36 Error Priority,
§46 Deterministic vs AI evaluation split.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import (
    AIMessage,
    AIMessageRole,
    AIRequest,
    AITask,
    ResponseFormat,
    ResponseFormatType,
)
from app.domains.ai.router import AIRouter
from app.domains.learning.contracts import IndependenceLevel
from app.domains.ramp.contracts import (
    ElaborationSignal,
    RampAttemptFeedback,
    RampCoachingAdvice,
    RampExerciseType,
    RampSampleAnswer,
    RampScore,
    RampSupportLevel,
    RampTaskSpec,
    SUPPORT_INDEPENDENCE_MULTIPLIER,
)
from app.domains.ramp.elaboration_engine import ElaborationEngine
from app.domains.ramp.prompts import RampPrompts


class RampEvaluator:
    """
    Hybrid evaluator: deterministic metrics + AI semantic evaluation.
    §46: deterministic for duration/pause/filler/independence;
         AI for semantic adequacy/naturalness/topic relevance/idea quality.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.elaboration_engine = ElaborationEngine()

    async def evaluate(
        self,
        task_spec: RampTaskSpec,
        user_transcript: str,
        support_level_used: int,
        audio_metrics: dict[str, Any] | None = None,
        response_latency_ms: float | None = None,
        used_hint: bool = False,
    ) -> tuple[RampScore, RampAttemptFeedback]:
        """
        Returns (RampScore, RampAttemptFeedback).
        §35 Stage-specific scoring weights.
        """
        stage = task_spec.stage
        transcript = user_transcript.strip()

        # ---------------------------------------------------------------------------
        # 1. Deterministic metrics (§46)
        # ---------------------------------------------------------------------------

        # Independence
        indep_mult = SUPPORT_INDEPENDENCE_MULTIPLIER.get(support_level_used, 0.5)
        is_independent = support_level_used == 0 and not used_hint
        independence_level = (
            IndependenceLevel.INDEPENDENT if is_independent
            else IndependenceLevel.ASSISTED_HINT if support_level_used <= 3
            else IndependenceLevel.SCAFFOLDED
        )

        # Elaboration signals
        signals = self.elaboration_engine.detect_signals(
            transcript=transcript,
            stage=stage,
            measured_level="N3",  # TODO: pass from session
        )

        # Has reason / example (deterministic)
        has_reason = self.elaboration_engine.has_reason(transcript)
        has_example = self.elaboration_engine.has_example(transcript)
        sentence_complete = self.elaboration_engine.is_sentence_complete(transcript)

        # Duration from audio_metrics
        speech_duration_ms: int | None = None
        filler_rate: float | None = None
        long_pause_count: int | None = None
        self_repair_count: int | None = None
        if audio_metrics:
            speech_duration_ms = audio_metrics.get("speech_duration_ms")
            filler_rate = audio_metrics.get("filler_rate")
            long_pause_count = audio_metrics.get("long_pause_count")
            self_repair_count = audio_metrics.get("self_repair_count")

        # ---------------------------------------------------------------------------
        # 2. AI semantic evaluation (§46)
        # ---------------------------------------------------------------------------
        ai_data: dict[str, Any] = {}
        if transcript:
            ai_data = await self._evaluate_with_ai(task_spec, transcript, support_level_used)

        semantic_relevance = ai_data.get("semantic_relevance", 70.0)
        naturalness = ai_data.get("naturalness", 70.0)
        grammar_score = ai_data.get("grammar_score", 70.0)
        completeness_ai = ai_data.get("completeness", 50.0)
        idea_quality = ai_data.get("idea_quality", 60.0)
        errors = ai_data.get("errors", [])
        correction_jp = ai_data.get("correction_jp")
        feedback_jp = ai_data.get("feedback_jp", "")

        # Override deterministic signals from AI (AI is authoritative for grammar)
        if ai_data:
            has_reason = ai_data.get("has_reason", has_reason)
            has_example = ai_data.get("has_example", has_example)
            sentence_complete = ai_data.get("sentence_complete", sentence_complete)

        # ---------------------------------------------------------------------------
        # 3. Compute sub-dimension scores
        # ---------------------------------------------------------------------------

        # Production accuracy (grammar + naturalness + relevance)
        production_accuracy = (grammar_score * 0.4 + naturalness * 0.3 + semantic_relevance * 0.3)

        # Independence score [0–100]
        independence_score = indep_mult * 100.0

        # Completeness (sentence complete + duration ratio)
        completeness = completeness_ai
        if not sentence_complete:
            completeness = min(completeness, 40.0)
        if ElaborationSignal.CONTENT_WORD_ONLY in signals:
            completeness = min(completeness, 30.0)

        # Fluency (from audio or estimated)
        if audio_metrics and speech_duration_ms:
            target_ms = task_spec.target_duration_sec * 1000
            duration_ratio = min(1.0, speech_duration_ms / max(target_ms, 1))
            filler_penalty = min(30.0, (filler_rate or 0) * 100)
            pause_penalty = min(20.0, (long_pause_count or 0) * 5)
            fluency = max(0.0, 70.0 + duration_ratio * 20.0 - filler_penalty - pause_penalty)
        else:
            # Text-only: estimate from sentence completeness
            fluency = 80.0 if sentence_complete else 50.0

        # Elaboration score
        elaboration = 50.0  # baseline
        if has_reason:
            elaboration += 25.0
        if has_example:
            elaboration += 25.0
        if ElaborationSignal.NO_REASON in signals and stage >= 5:
            elaboration -= 20.0
        if ElaborationSignal.NO_EXAMPLE in signals and stage >= 6:
            elaboration -= 15.0
        elaboration = max(0.0, min(100.0, elaboration))

        # Reaction (response latency)
        if response_latency_ms is not None:
            # 0–2s → 100, 2–5s → 80–60, >5s → penalty
            if response_latency_ms < 2000:
                reaction = 100.0
            elif response_latency_ms < 5000:
                reaction = 100.0 - (response_latency_ms - 2000) / 3000 * 40
            else:
                reaction = max(20.0, 60.0 - (response_latency_ms - 5000) / 5000 * 40)
        else:
            reaction = 70.0  # unknown latency — neutral

        # Stage-specific weight override (§35)
        score = self._compute_stage_score(
            stage=stage,
            production_accuracy=production_accuracy,
            independence=independence_score,
            completeness=completeness,
            fluency=fluency,
            elaboration=elaboration,
            reaction=reaction,
            support_level_used=support_level_used,
            sentence_count=self._count_sentences(transcript),
            idea_count=int(idea_quality / 25),  # rough proxy
            speech_duration_ms=speech_duration_ms,
            filler_rate=filler_rate,
            long_pause_count=long_pause_count,
            self_repair_count=self_repair_count,
            response_latency_ms=response_latency_ms,
            independence_level=independence_level.value,
        )

        # ---------------------------------------------------------------------------
        # 4. Build sample answers & coaching advice
        # ---------------------------------------------------------------------------
        sample_answers: list[RampSampleAnswer] = []
        raw_samples = ai_data.get("sample_answers", [])
        if isinstance(raw_samples, list):
            for s in raw_samples:
                if isinstance(s, dict) and s.get("japanese") and s.get("vietnamese"):
                    sample_answers.append(
                        RampSampleAnswer(
                            style=s.get("style", "casual"),
                            style_label=s.get("style_label", "Thường ngày"),
                            japanese=s.get("japanese", ""),
                            vietnamese=s.get("vietnamese", ""),
                            nuance=s.get("nuance"),
                        )
                    )

        if not sample_answers:
            sample_answers = self._generate_fallback_sample_answers(task_spec, transcript)

        coaching_advice: RampCoachingAdvice | None = None
        raw_advice = ai_data.get("coaching_advice")
        if isinstance(raw_advice, dict):
            coaching_advice = RampCoachingAdvice(
                overall_comment=raw_advice.get("overall_comment"),
                strengths=raw_advice.get("strengths", []),
                improvements=raw_advice.get("improvements", []),
                grammar_notes=raw_advice.get("grammar_notes", []),
            )
        if not coaching_advice:
            coaching_advice = self._generate_fallback_coaching_advice(score, sentence_complete, has_reason)

        # ---------------------------------------------------------------------------
        # 5. Build feedback (§37)
        # ---------------------------------------------------------------------------
        feedback = self._build_feedback(
            score=score,
            signals=signals,
            has_reason=has_reason,
            has_example=has_example,
            sentence_complete=sentence_complete,
            correction_jp=correction_jp,
            feedback_jp=feedback_jp,
            stage=stage,
            sample_answers=sample_answers,
            coaching_advice=coaching_advice,
        )

        return score, feedback

    def _generate_fallback_sample_answers(self, task_spec: RampTaskSpec, transcript: str) -> list[RampSampleAnswer]:
        """Generate deterministic fallback sample answer variations."""
        base_jp = task_spec.echo_sentence or task_spec.template_sentence or task_spec.seed_sentence or transcript or "はい、そうです。"
        return [
            RampSampleAnswer(
                style="casual",
                style_label="Thường ngày (Casual)",
                japanese=base_jp,
                vietnamese="Cách nói tự nhiên, phù hợp trong giao tiếp bạn bè hàng ngày.",
                nuance="Thân mật, phản xạ nhanh và gọn gàng.",
            ),
            RampSampleAnswer(
                style="polite",
                style_label="Lịch sự (Polite/Business)",
                japanese=f"{base_jp.rstrip('。')}と思います。" if not base_jp.endswith("です。") and not base_jp.endswith("ます。") else base_jp,
                vietnamese="Cách nói lịch sự chuẩn mực, phù hợp trong môi trường công sở.",
                nuance="Dùng thể です/ます và cách đệm ý trang nhã.",
            ),
            RampSampleAnswer(
                style="advanced",
                style_label="Mở rộng ý (Advanced)",
                japanese=f"{base_jp.rstrip('。')}。なぜなら、とても大切だからです。",
                vietnamese="Cách diễn đạt nâng cao: bổ sung thêm lý do hoặc giải thích để bài nói có chiều sâu.",
                nuance="Mở rộng cấu trúc câu giúp bài phát ngôn lưu loát và tự nhiên.",
            ),
        ]

    def _generate_fallback_coaching_advice(self, score: RampScore, sentence_complete: bool, has_reason: bool) -> RampCoachingAdvice:
        """Generate structured default coaching advice."""
        strengths: list[str] = []
        improvements: list[str] = []
        grammar_notes: list[str] = []

        if score.production_accuracy >= 70:
            strengths.append("Ý tứ rõ ràng, người bản xứ có thể nắm bắt thông tin ngay lập tức.")
        if score.fluency >= 70:
            strengths.append("Tốc độ phản xạ và độ trôi chảy tốt, hạn chế được quãng ngắt dài.")
        if not strengths:
            strengths.append("Dũng cảm phản xạ phát ngôn và hoàn thành thử thách nấc thang.")

        if not sentence_complete:
            improvements.append("Hãy chú ý kết thúc câu trọn vẹn bằng trợ từ và vị ngữ rõ ràng (〜です / 〜ます).")
        if not has_reason:
            improvements.append("Hãy thử thách bản thân nối thêm 1 câu lý do với 「〜から」 hoặc 「〜ので」 để tăng chiều sâu.")
        if not improvements:
            improvements.append("Tiếp tục duy trì nhịp độ và thử sức với các nấc thang cao hơn.")

        grammar_notes.append("Luyện tập ngắt nhịp phách Mora đều đặn để câu tiếng Nhật nghe tự nhiên hơn.")

        return RampCoachingAdvice(
            overall_comment="Bạn đang xây dựng phản xạ nói rất tốt! Hãy tham khảo các gợi ý trả lời phía trên để mở rộng vốn câu.",
            strengths=strengths,
            improvements=improvements,
            grammar_notes=grammar_notes,
        )

    def _compute_stage_score(self, stage: int, **kwargs: Any) -> RampScore:
        """§35 Stage-specific scoring weights."""
        if stage <= 2:
            # Early: accuracy + completeness dominate
            return RampScore.compute(
                production_accuracy=kwargs["production_accuracy"],
                independence=kwargs["independence"] * 0.8,  # less weight early
                completeness=kwargs["completeness"],
                fluency=kwargs["fluency"] * 0.7,
                elaboration=kwargs["elaboration"] * 0.5,
                reaction=kwargs["reaction"] * 0.8,
                **{k: v for k, v in kwargs.items() if k not in (
                    "production_accuracy", "independence", "completeness",
                    "fluency", "elaboration", "reaction"
                )},
            )
        elif stage <= 6:
            # Middle: elaboration + independence matter more
            return RampScore.compute(**kwargs)
        else:
            # Advanced: fluency + independence + coherence
            adjusted = dict(kwargs)
            adjusted["fluency"] = kwargs["fluency"] * 1.15
            adjusted["independence"] = kwargs["independence"] * 1.1
            adjusted["elaboration"] = kwargs["elaboration"] * 1.15
            adjusted["fluency"] = min(100.0, adjusted["fluency"])
            adjusted["independence"] = min(100.0, adjusted["independence"])
            adjusted["elaboration"] = min(100.0, adjusted["elaboration"])
            return RampScore.compute(**adjusted)

    def _build_feedback(
        self,
        score: RampScore,
        signals: list[ElaborationSignal],
        has_reason: bool,
        has_example: bool,
        sentence_complete: bool,
        correction_jp: str | None,
        feedback_jp: str,
        stage: int,
        sample_answers: list[RampSampleAnswer] | None = None,
        coaching_advice: RampCoachingAdvice | None = None,
    ) -> RampAttemptFeedback:
        """Build RampAttemptFeedback with badges and next action. §37"""
        badges: list[str] = []
        next_action = "next"

        if score.production_accuracy >= 70:
            badges.append("✅ 意味が伝わった")
        if score.production_accuracy >= 80:
            badges.append("✅ 文法OK")

        too_short = ElaborationSignal.TOO_SHORT in signals
        incomplete = (
            not sentence_complete
            or ElaborationSignal.INCOMPLETE_SENTENCE in signals
            or ElaborationSignal.CONTENT_WORD_ONLY in signals
        )

        if incomplete:
            badges.append("⚠️ 文が不完全")
            next_action = "retry"
        elif too_short:
            badges.append("⚠️ 短すぎ")
            next_action = "elaborate"

        if not has_reason and stage >= 5:
            badges.append("🎯 理由を足してみよう")
            next_action = "elaborate"
        if not has_example and stage >= 6:
            badges.append("🎯 例を挙げてみよう")
            next_action = "elaborate"

        if score.overall >= 75 and not signals:
            next_action = "next"

        # Elaboration cue
        elab_prompt = None
        if signals:
            step = 1
            if ElaborationSignal.NO_REASON in signals:
                step = 2
            elif ElaborationSignal.NO_EXAMPLE in signals:
                step = 3
            elab_engine = ElaborationEngine()
            elab_prompt = elab_engine.build_elaboration_prompt(signals, stage, step)

        return RampAttemptFeedback(
            meaning_clear=score.production_accuracy >= 70,
            grammar_ok=score.production_accuracy >= 80,
            too_short=too_short,
            missing_reason=not has_reason and stage >= 5,
            missing_example=not has_example and stage >= 6,
            incomplete_sentence=incomplete,
            elaboration_prompt=elab_prompt,
            correction=correction_jp,
            badges=badges,
            next_action=next_action,
            ramp_score=score,
            sample_answers=sample_answers or [],
            coaching_advice=coaching_advice,
        )

    async def _evaluate_with_ai(
        self,
        task_spec: RampTaskSpec,
        transcript: str,
        support_level: int,
    ) -> dict[str, Any]:
        """AI semantic evaluation with fallback to empty dict."""
        try:
            sys_p, usr_p = RampPrompts.build_semantic_evaluation_prompt(
                topic=task_spec.topic,
                prompt_jp=task_spec.prompt_jp,
                exercise_type=task_spec.exercise_type.value,
                stage=task_spec.stage,
                user_transcript=transcript,
                support_level=support_level,
            )
            req = AIRequest(
                messages=[AIMessage(role=AIMessageRole.USER, content=usr_p)],
                task=AITask.RAMP_SEMANTIC_EVALUATION,
                system_instruction=sys_p,
                temperature=0.3,
                max_output_tokens=500,
                response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            )
            resp = await self.ai_router.generate(req)
            return json.loads(resp.text)
        except Exception as e:
            logger.warning(f"[RampEvaluator] AI evaluation failed: {e}")
            return {}

    def _count_sentences(self, text: str) -> int:
        """Count approximate sentence count."""
        return max(1, len(re.findall(r"[。！？]", text)) or (1 if text.strip() else 0))
