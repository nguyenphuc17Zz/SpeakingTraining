import base64
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learner_memory.merger import MemoryMerger
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.pronunciation.contracts import (
    PronunciationAnalysisPolicy,
    PronunciationResult,
    PronunciationTarget,
    ReferenceType,
    TargetType,
)
from app.domains.pronunciation.learning_signal_extractor import PronunciationLearningSignalExtractor
from app.domains.pronunciation.models import PronunciationAttempt, PronunciationPracticeTarget
from app.domains.pronunciation.pipeline import PronunciationPipeline
from app.domains.pronunciation.queue import pronunciation_job_queue
from app.domains.pronunciation.schemas import (
    PronunciationAttemptResponse,
    PronunciationHistoryItemDTO,
    PronunciationPracticeTargetDTO,
    PronunciationSummaryStatsDTO,
)
from app.domains.speech.contracts import STTOptions
from app.domains.speech.stt_router import stt_router
from app.domains.users.service import UserService
from app.shared.errors.exceptions import NotFoundException, ValidationException


class PronunciationService:
    """Core domain service for orchestrating Japanese Pronunciation analysis, persistent attempts, and learning signal ingestion."""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session
        self.user_service = UserService(db_session)

    async def analyze_audio(
        self,
        user_id: str,
        audio_bytes: bytes,
        target_text: str,
        expected_reading: str | None = None,
        target_type: TargetType = TargetType.SENTENCE,
        reference_type: ReferenceType = ReferenceType.SYNTHETIC,
        voicevox_speaker_id: int | None = 1,
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> PronunciationAttemptResponse:
        """
        Executes end-to-end pronunciation analysis:
        1. STT transcription (to capture word timestamps)
        2. Pronunciation pipeline execution
        3. Persist PronunciationAttempt
        4. Extract learning signals and merge into LearnerMemory (Phase 5)
        5. Recalculate LearnerProfile
        """
        if not target_text or not target_text.strip():
            raise ValidationException("Target text cannot be empty.")

        target = PronunciationTarget(
            reference_text=target_text.strip(),
            expected_reading=expected_reading,
            target_type=target_type,
            reference_type=reference_type,
            voicevox_speaker_id=voicevox_speaker_id,
        )

        # 1. High-accuracy STT transcription anchored by target reference text
        user_transcript = None
        word_timestamps = None
        try:
            from app.domains.speech.model_manager import whisper_model_manager
            active_model = whisper_model_manager.get_active_model_id()
            ref_clean = target_text.strip()
            prompt = f"日本語のシャドーイング練習、発音評価。手本：「{ref_clean}」"
            stt_opts = STTOptions(
                language="ja",
                model=active_model,
                beam_size=5,
                vad_filter=True,
                initial_prompt=prompt,
            )
            stt_res = await stt_router.transcribe(audio_bytes=audio_bytes, options=stt_opts)
            user_transcript = stt_res.text.strip()
            word_timestamps = stt_res.words
        except Exception as se:
            logger.warning(f"[PronunciationService] STT transcription failed: {se}. Proceeding without word timestamps.")

        # 2. Run Pronunciation Pipeline
        pipeline_res: PronunciationResult = await PronunciationPipeline.run(
            audio_bytes=audio_bytes,
            target=target,
            user_transcript=user_transcript,
            word_timestamps=word_timestamps,
            policy=PronunciationAnalysisPolicy.DEEP,
        )

        # 3. Persist PronunciationAttempt record
        attempt = PronunciationAttempt(
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            reference_text=target_text.strip(),
            expected_reading=expected_reading,
            user_text=user_transcript,
            target_type=target_type.value,
            reference_type=reference_type.value,
            analysis_status="completed",
            overall_score=pipeline_res.overall_score,
            overall_confidence=pipeline_res.overall_confidence.value,
            score_interpretation=pipeline_res.score_interpretation,
            engine_version=pipeline_res.engine_version,
            scores_json={
                "overall": pipeline_res.overall_score,
                "phoneme": pipeline_res.phoneme_score.model_dump() if pipeline_res.phoneme_score else None,
                "mora": pipeline_res.mora_timing_score.model_dump() if pipeline_res.mora_timing_score else None,
                "pitch": pipeline_res.pitch_score.model_dump() if pipeline_res.pitch_score else None,
                "rhythm": pipeline_res.rhythm_score.model_dump() if pipeline_res.rhythm_score else None,
                "intonation": pipeline_res.intonation_score.model_dump() if pipeline_res.intonation_score else None,
            },
            feedback_json={
                "top_issues": [i.model_dump() for i in pipeline_res.top_issues],
                "strengths": pipeline_res.strengths,
                "practice_recommendation": pipeline_res.practice_recommendation,
                "partial_reasons": pipeline_res.partial_reasons,
            },
            acoustic_metadata_json={
                "phoneme_assessment": [p.model_dump() for p in (pipeline_res.phoneme_assessment or [])],
                "mora_assessment": pipeline_res.mora_assessment.model_dump() if pipeline_res.mora_assessment else None,
                "pitch_assessment": pipeline_res.pitch_assessment.model_dump() if pipeline_res.pitch_assessment else None,
                "rhythm_assessment": pipeline_res.rhythm_assessment.model_dump() if pipeline_res.rhythm_assessment else None,
                "intonation_assessment": pipeline_res.intonation_assessment.model_dump() if pipeline_res.intonation_assessment else None,
                "audio_quality": pipeline_res.audio_quality.model_dump() if pipeline_res.audio_quality else None,
            },
        )

        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)

        # 4. Ingest Learning Signals into Learner Memory (Phase 5 integration)
        try:
            candidates = PronunciationLearningSignalExtractor.extract_from_pronunciation_result(
                result=pipeline_res,
                user_id=user_id,
                session_id=session_id,
                turn_id=turn_id,
                context_tag="pronunciation_practice" if not session_id else "conversation_speech",
            )
            if candidates:
                merger = MemoryMerger(self.session)
                await merger.merge_candidates(user_id=user_id, candidates=candidates)
                profile_service = LearnerProfileService(self.session)
                await profile_service.recalculate_profile(user_id=user_id, generate_ai_summary=False)
                logger.info(f"[PronunciationService] Merged {len(candidates)} pronunciation signals into learner profile.")
        except Exception as me:
            logger.warning(f"[PronunciationService] Memory signal ingestion failed: {me}", exc_info=True)

        return self._to_attempt_response(attempt, pipeline_res)

    async def enqueue_analysis(
        self,
        user_id: str,
        audio_bytes: bytes,
        target_text: str,
        expected_reading: str | None = None,
        target_type: TargetType = TargetType.SENTENCE,
        reference_type: ReferenceType = ReferenceType.SYNTHETIC,
        session_id: str | None = None,
        turn_id: str | None = None,
    ) -> str:
        """Saves a pending attempt and enqueues to the background worker."""
        attempt = PronunciationAttempt(
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            reference_text=target_text.strip(),
            expected_reading=expected_reading,
            target_type=target_type.value,
            reference_type=reference_type.value,
            analysis_status="pending",
        )
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)

        job_payload = {
            "attempt_id": attempt.id,
            "user_id": user_id,
            "target_text": target_text,
            "expected_reading": expected_reading,
            "target_type": target_type.value,
            "reference_type": reference_type.value,
            "session_id": session_id,
            "turn_id": turn_id,
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        }
        await pronunciation_job_queue.enqueue(job_payload)
        logger.info(f"[PronunciationService] Enqueued attempt '{attempt.id}' for background processing.")
        return attempt.id

    async def get_attempt(self, attempt_id: str) -> PronunciationAttemptResponse:
        """Fetches attempt with its structured pronunciation result."""
        stmt = select(PronunciationAttempt).where(PronunciationAttempt.id == attempt_id)
        res = await self.session.execute(stmt)
        attempt = res.scalar_one_or_none()
        if not attempt:
            raise NotFoundException(f"Pronunciation attempt with ID '{attempt_id}' not found.")

        return self._to_attempt_response(attempt)

    async def get_user_history(
        self, user_id: str, limit: int = 20
    ) -> list[PronunciationHistoryItemDTO]:
        """Retrieves recent pronunciation attempts history."""
        stmt = (
            select(PronunciationAttempt)
            .where(PronunciationAttempt.user_id == user_id)
            .order_by(desc(PronunciationAttempt.created_at))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        attempts = res.scalars().all()
        return [
            PronunciationHistoryItemDTO(
                id=a.id,
                reference_text=a.reference_text,
                target_type=a.target_type,
                overall_score=a.overall_score,
                score_interpretation=a.score_interpretation,
                analysis_status=a.analysis_status,
                created_at=a.created_at,
            )
            for a in attempts
        ]

    async def get_user_summary_stats(self, user_id: str) -> PronunciationSummaryStatsDTO:
        """Calculates aggregate pronunciation performance across recent attempts."""
        stmt = (
            select(PronunciationAttempt)
            .where(PronunciationAttempt.user_id == user_id, PronunciationAttempt.analysis_status == "completed")
            .order_by(desc(PronunciationAttempt.created_at))
            .limit(30)
        )
        res = await self.session.execute(stmt)
        attempts = res.scalars().all()

        if not attempts:
            return PronunciationSummaryStatsDTO(
                total_attempts=0,
                avg_overall_score=0.0,
                avg_mora_score=0.0,
                avg_pitch_score=0.0,
                avg_phoneme_score=0.0,
                top_weaknesses=[],
                recent_trend="new",
            )

        overall_scores = [a.overall_score for a in attempts if a.overall_score is not None]
        avg_overall = float(sum(overall_scores) / len(overall_scores)) if overall_scores else 0.0

        # Subscore averages
        mora_scores = []
        pitch_scores = []
        phoneme_scores = []

        for a in attempts:
            if a.scores_json:
                if a.scores_json.get("mora"):
                    mora_scores.append(a.scores_json["mora"]["score"])
                if a.scores_json.get("pitch"):
                    pitch_scores.append(a.scores_json["pitch"]["score"])
                if a.scores_json.get("phoneme"):
                    phoneme_scores.append(a.scores_json["phoneme"]["score"])

        avg_mora = float(sum(mora_scores) / len(mora_scores)) if mora_scores else avg_overall
        avg_pitch = float(sum(pitch_scores) / len(pitch_scores)) if pitch_scores else avg_overall
        avg_phoneme = float(sum(phoneme_scores) / len(phoneme_scores)) if phoneme_scores else avg_overall

        # Simple trend
        recent_trend = "stable"
        if len(overall_scores) >= 4:
            first_half = overall_scores[-len(overall_scores)//2:]
            second_half = overall_scores[:len(overall_scores)//2]
            delta = (sum(second_half)/len(second_half)) - (sum(first_half)/len(first_half))
            if delta >= 3.0:
                recent_trend = "improving"
            elif delta <= -3.0:
                recent_trend = "worsening"

        return PronunciationSummaryStatsDTO(
            total_attempts=len(attempts),
            avg_overall_score=round(avg_overall, 1),
            avg_mora_score=round(avg_mora, 1),
            avg_pitch_score=round(avg_pitch, 1),
            avg_phoneme_score=round(avg_phoneme, 1),
            top_weaknesses=["Trường âm (Long Vowels)", "Cao độ Heiban", "Âm ngắt っ"] if avg_mora < 75 else ["Cao độ Tokyo"],
            recent_trend=recent_trend,
        )

    async def get_practice_targets(
        self, user_id: str | None = None, limit: int = 6
    ) -> list[PronunciationPracticeTargetDTO]:
        """Returns practice targets, seeding defaults if table is empty."""
        stmt = select(PronunciationPracticeTarget).limit(limit)
        res = await self.session.execute(stmt)
        targets = res.scalars().all()

        if not targets:
            await self.seed_default_practice_targets()
            stmt2 = select(PronunciationPracticeTarget).limit(limit)
            res2 = await self.session.execute(stmt2)
            targets = res2.scalars().all()

        return [
            PronunciationPracticeTargetDTO(
                id=t.id,
                target_text=t.target_text,
                target_reading=t.target_reading,
                target_type=t.target_type,
                difficulty=t.difficulty,
                weak_area_key=t.weak_area_key,
                category=t.category,
                hint=t.hint,
            )
            for t in targets
        ]

    async def seed_default_practice_targets(self) -> None:
        """Seeds foundational Japanese pronunciation challenge items."""
        default_items = [
            PronunciationPracticeTarget(
                target_text="学校",
                target_reading="がっこう",
                target_type="word",
                difficulty="beginner",
                weak_area_key="pronunciation.small_tsu",
                category="mora_timing",
                hint="Chú ý âm ngắt「っ」chiếm 1 nhịp tĩnh và trường âm「う」ở cuối từ.",
            ),
            PronunciationPracticeTarget(
                target_text="おばあさん",
                target_reading="おばあさん",
                target_type="word",
                difficulty="beginner",
                weak_area_key="pronunciation.long_vowel",
                category="long_vowel",
                hint="Trường âm「ああ」kéo dài đúng 2 mora, phân biệt với 'おばさん'.",
            ),
            PronunciationPracticeTarget(
                target_text="切手",
                target_reading="きって",
                target_type="word",
                difficulty="beginner",
                weak_area_key="pronunciation.small_tsu",
                category="sokuon",
                hint="Phân biệt 'きって' (tem thư) và 'きて' (hãy đến).",
            ),
            PronunciationPracticeTarget(
                target_text="新聞",
                target_reading="しんぶん",
                target_type="word",
                difficulty="beginner",
                weak_area_key="pronunciation.n_sound",
                category="nasal",
                hint="Gồm 4 mora trọn vẹn: し・ん・ぶ・ん.",
            ),
            PronunciationPracticeTarget(
                target_text="雨が降っています",
                target_reading="あめがふっています",
                target_type="sentence",
                difficulty="intermediate",
                weak_area_key="pitch_accent.atamadaka",
                category="pitch",
                hint="Từ '雨' (mưa) có trọng âm Atamadaka (cao ở âm 'あ', hạ ở 'め').",
            ),
            PronunciationPracticeTarget(
                target_text="きょうは映画を見ました",
                target_reading="きょうはえいがをみました",
                target_type="sentence",
                difficulty="intermediate",
                weak_area_key="pronunciation.long_vowel",
                category="sentence",
                hint="Câu hoàn chỉnh kết hợp trường âm (きょう, えいが) và cao độ tự nhiên.",
            ),
        ]
        for item in default_items:
            self.session.add(item)
        await self.session.commit()
        logger.info(f"[PronunciationService] Seeded {len(default_items)} default pronunciation practice targets.")

    @staticmethod
    def _to_attempt_response(
        attempt: PronunciationAttempt, result: PronunciationResult | None = None
    ) -> PronunciationAttemptResponse:
        """Converts DB model to API response DTO."""
        top_issues = []
        strengths = []
        recommendation = None
        if attempt.feedback_json:
            top_issues = attempt.feedback_json.get("top_issues", [])
            strengths = attempt.feedback_json.get("strengths", [])
            recommendation = attempt.feedback_json.get("practice_recommendation")

        return PronunciationAttemptResponse(
            id=attempt.id,
            user_id=attempt.user_id,
            session_id=attempt.session_id,
            turn_id=attempt.turn_id,
            reference_text=attempt.reference_text,
            expected_reading=attempt.expected_reading,
            user_text=attempt.user_text,
            target_type=attempt.target_type,
            reference_type=attempt.reference_type,
            analysis_status=attempt.analysis_status,
            overall_score=attempt.overall_score,
            overall_confidence=attempt.overall_confidence,
            score_interpretation=attempt.score_interpretation,
            engine_version=attempt.engine_version,
            result=result,
            top_issues=top_issues,
            strengths=strengths,
            practice_recommendation=recommendation,
            error_message=attempt.error_message,
            created_at=attempt.created_at,
            updated_at=attempt.updated_at,
        )
