import base64
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AIResponse, AITask
from app.domains.ai.router import AIRouter
from app.domains.conversation.context import ConversationContextManager
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation.schemas import (
    AudioTurnResponse,
    ConversationRecentSessionRead,
    ConversationSessionCreate,
    ConversationSessionRead,
    ConversationSessionSummary,
    ConversationTurnRead,
)
from app.domains.conversation_intelligence.service import ConversationIntelligenceService
from app.domains.learner_memory.retriever import MemoryRetriever
from app.domains.personas.models import Persona
from app.domains.settings.service import SettingsService
from app.domains.audio import TTSRequest, VoiceService, tts_service
from app.domains.speech.contracts import STTOptions, TTSOptions
from app.domains.speech.errors import SpeechError
from app.domains.speech.stt_router import stt_router
from app.domains.users.service import UserService
from app.shared.errors.exceptions import NotFoundException, ValidationException


class ConversationService:
    """Core domain service for orchestrating Japanese Voice Sessions and Turn progression."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ai_router = AIRouter(session)
        self.settings_service = SettingsService(session)
        self.user_service = UserService(session)
        self.intelligence_service = ConversationIntelligenceService(session)
        self.memory_retriever = MemoryRetriever(session)
        self.context_manager = ConversationContextManager()

    async def _get_persona_or_404(self, persona_id: str) -> Persona:
        stmt = select(Persona).where(Persona.id == persona_id)
        res = await self.session.execute(stmt)
        persona = res.scalar_one_or_none()
        if not persona:
            raise NotFoundException(f"Persona with ID '{persona_id}' not found.")
        return persona

    async def _get_session_with_turns_or_404(self, session_id: str) -> ConversationSession:
        stmt = (
            select(ConversationSession)
            .where(ConversationSession.id == session_id)
            .options(
                selectinload(ConversationSession.turns),
                selectinload(ConversationSession.persona),
            )
        )
        res = await self.session.execute(stmt)
        conv_session = res.scalar_one_or_none()
        if not conv_session:
            raise NotFoundException(f"Conversation session with ID '{session_id}' not found.")
        return conv_session

    async def start_session(
        self,
        create_dto: ConversationSessionCreate,
        user_id: str | None = None,
    ) -> ConversationSessionRead:
        """Initializes a new ConversationSession with frozen configuration snapshots and an AI opening greeting."""
        resolved_user_id = user_id or (await self.user_service.get_or_create_default_user()).id
        persona = await self._get_persona_or_404(create_dto.persona_id)
        user_settings = await self.settings_service.get_or_create_settings(resolved_user_id)

        # Snapshot preferences (fallback to user settings defaults if not specified)
        ai_provider = create_dto.provider_preference or user_settings.default_ai_provider
        ai_model = create_dto.model_preference or user_settings.default_ai_model
        stt_provider = create_dto.stt_provider_preference or "faster_whisper"
        stt_model = create_dto.stt_model_preference or "base"

        # Resolve voice via VoiceService hierarchy
        voice_service = VoiceService(self.session)
        tts_provider, tts_voice, _, _ = await voice_service.resolve_voice_configuration(
            user_id=resolved_user_id,
            persona=persona,
            session_override_provider=create_dto.tts_provider_preference,
            session_override_voice=create_dto.tts_voice_preference,
        )

        conv_session = ConversationSession(
            user_id=resolved_user_id,
            persona_id=persona.id,
            mode=create_dto.mode,
            status="active",
            provider_preference=ai_provider,
            model_preference=ai_model,
            stt_provider_preference=stt_provider,
            stt_model_preference=stt_model,
            tts_provider_preference=tts_provider,
            tts_voice_preference=tts_voice,
            started_at=datetime.now(timezone.utc),
        )

        self.session.add(conv_session)
        await self.session.flush()

        # 1. Generate Persona Opening Greeting Turn
        opening_text = None
        try:
            opening_prompt = (
                f"You are roleplaying as {persona.name} (Role: {persona.role}). "
                f"Description: {persona.description}. "
                f"Speaking style: {persona.speaking_style}. "
                f"Difficulty level: {persona.difficulty}. "
                f"System Prompt: {persona.system_prompt or ''}\n\n"
                f"The learner is entering the speaking room to have a conversation with you. "
                f"Say a natural, friendly, welcoming opening greeting in Japanese (1-2 sentences) "
                f"that fits your role and initiates the conversation (e.g. asking how they are doing or inviting them to chat). "
                f"IMPORTANT: Output ONLY the Japanese spoken sentence. Do not include romaji, translation, greetings to AI, or explanation."
            )
            ai_req = AIRequest(
                task=AITask.CONVERSATION,
                messages=[AIMessage(role=AIMessageRole.USER, content=opening_prompt)],
                system_instruction=persona.system_prompt or "You are a Japanese conversation partner.",
                temperature=0.7,
                max_output_tokens=100,
                provider=conv_session.provider_preference,
                model=conv_session.model_preference,
            )
            ai_res: AIResponse = await self.ai_router.generate(
                task=AITask.CONVERSATION,
                request=ai_req,
                user_id=resolved_user_id,
            )
            if ai_res and ai_res.text:
                cleaned = ai_res.text.strip().replace('"', '').replace('「', '').replace('」', '')
                if cleaned:
                    opening_text = cleaned
        except Exception as e:
            logger.warning(f"[Conversation] AI opening greeting generation failed: {e}")

        # Fallback opening greeting if AI generation fails
        if not opening_text:
            role_lower = persona.role.lower()
            name_lower = persona.name.lower()
            if "ramen" in role_lower or "chef" in role_lower or "quán" in role_lower:
                opening_text = "いらっしゃい！何にする？今日のおすすめは特製ラーメンだよ！"
            elif "senpai" in name_lower or "senpai" in role_lower:
                opening_text = f"あ、お疲れ様！今日も日本語の練習頑張ろうね。最近どう？"
            elif "sensei" in name_lower or "sensei" in role_lower or "teacher" in role_lower or "giáo viên" in role_lower:
                opening_text = f"こんにちは。今日の日本語レッスンを始めましょう。調子はいかがですか？"
            elif "doctor" in role_lower or "bác sĩ" in role_lower:
                opening_text = "こんにちは。今日はどうされましたか？どこか具合が悪いですか？"
            else:
                opening_text = f"こんにちは！{persona.name}です。一緒に楽しく日本語で話しましょう！"

        # 2. Create and commit Turn 1 (Assistant Opening)
        opening_turn = ConversationTurn(
            session_id=conv_session.id,
            sequence=1,
            speaker="assistant",
            transcript=opening_text,
            ai_provider=conv_session.provider_preference or "gemini",
            ai_model=conv_session.model_preference or "gemini-1.5-flash",
            tts_provider=conv_session.tts_provider_preference,
            tts_voice=conv_session.tts_voice_preference,
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(opening_turn)
        await self.session.commit()

        # 3. Synthesize opening turn audio if TTS enabled
        opening_audio_base64 = None
        tts_provider_used = (conv_session.tts_provider_preference or "voicevox").lower().strip()
        if tts_provider_used not in ("none", "off", "disabled", "web_speech"):
            try:
                tts_req = TTSRequest(
                    text=opening_text,
                    provider=tts_provider_used,
                    voice_id=conv_session.tts_voice_preference or "1",
                    user_id=conv_session.user_id,
                    allow_fallback=True,
                )
                tts_output = await tts_service.synthesize(tts_req)
                opening_audio_base64 = tts_output.audio_base64
            except Exception as tts_err:
                logger.warning(f"[Conversation] Opening greeting TTS synthesis failed: {tts_err}")

        logger.info(
            f"[Conversation] Started session '{conv_session.id}' with persona '{persona.name}' and opening greeting: '{opening_text}'"
        )
        session_read = await self.get_session(conv_session.id)
        session_read.opening_audio_base64 = opening_audio_base64
        session_read.opening_audio_format = "wav"
        return session_read

    async def get_session(self, session_id: str) -> ConversationSessionRead:
        """Retrieve conversation session with its turn history."""
        conv_session = await self._get_session_with_turns_or_404(session_id)
        return ConversationSessionRead.model_validate(conv_session)

    async def process_audio_turn(
        self,
        session_id: str,
        audio_bytes: bytes,
        client_turn_id: str | None = None,
        browser_transcript: str | None = None,
        user_id: str | None = None,
    ) -> AudioTurnResponse:
        """End-to-end voice turn pipeline: Audio ➔ STT ➔ AI Context ➔ AI Router ➔ TTS ➔ DB Turn Persistence."""
        conv_session = await self._get_session_with_turns_or_404(session_id)
        if conv_session.status != "active":
            raise ValidationException(f"Cannot add turn to inactive session (status: {conv_session.status})")

        resolved_user_id = user_id or conv_session.user_id

        # Anti-duplicate check
        if client_turn_id:
            for turn in conv_session.turns:
                if turn.client_turn_id == client_turn_id and turn.speaker == "assistant":
                    logger.info(f"[Conversation] Duplicate client_turn_id '{client_turn_id}' detected. Returning existing turn.")
                    user_turn_prev = next((t for t in conv_session.turns if t.sequence == turn.sequence - 1), turn)
                    return AudioTurnResponse(
                        session_id=conv_session.id,
                        user_turn=ConversationTurnRead.model_validate(user_turn_prev),
                        assistant_turn=ConversationTurnRead.model_validate(turn),
                        audio_base64=None,
                        audio_format="wav",
                        metrics=turn.metrics or {},
                    )

        total_turn_start = time.perf_counter()

        # 1. Transcribe Audio (STT with Smart WebSpeech Fallback)
        user_text = ""
        stt_ms = 0
        stt_provider_name = conv_session.stt_provider_preference or "faster_whisper"
        stt_model_name = conv_session.stt_model_preference or "base"
        stt_confidence = 1.0

        cleaned_browser = browser_transcript.strip() if browser_transcript else ""

        if (conv_session.stt_provider_preference or "").lower() == "web_speech" and cleaned_browser:
            user_text = cleaned_browser
            stt_provider_name = "web_speech"
            stt_model_name = "google-webspeech"
            stt_ms = 10
        else:
            try:
                stt_opts = STTOptions(
                    model=conv_session.stt_model_preference or "base",
                    language="ja",
                    beam_size=5,
                    vad_filter=True,
                    initial_prompt="こんにちは。日本語の会話です。正確に認識してください。",
                )
                stt_result = await stt_router.transcribe(
                    audio_bytes=audio_bytes,
                    provider_id=conv_session.stt_provider_preference,
                    options=stt_opts,
                )
                stt_ms = stt_result.processing_time_ms or 0
                stt_provider_name = stt_result.provider
                stt_model_name = stt_result.model
                stt_confidence = stt_result.confidence or 1.0
                user_text = stt_result.text.strip()
            except Exception as e:
                logger.warning(f"[Conversation] Local STT failed ({e}), checking browser transcript fallback...")
                user_text = ""

            # If Whisper returned empty or severely truncated text, fallback to browser transcript
            if not user_text or (cleaned_browser and len(user_text) < 2 and len(cleaned_browser) > 3):
                if cleaned_browser:
                    logger.info(f"[Conversation] Using browser transcript fallback: '{cleaned_browser}'")
                    user_text = cleaned_browser
                    stt_provider_name = f"{stt_provider_name}+fallback"

        if not user_text:
            # Handle empty / unintelligible audio gracefully
            user_text = "（音声が聞き取れませんでした）"

        # 2. Persist User Turn
        current_max_seq = max([t.sequence for t in conv_session.turns], default=0)
        user_turn_seq = current_max_seq + 1
        user_turn_start_time = datetime.now(timezone.utc)

        speech_duration_ms = 0
        if "stt_result" in locals() and getattr(stt_result, "duration_ms", None):
            speech_duration_ms = int(stt_result.duration_ms)
        elif len(audio_bytes) > 44:
            speech_duration_ms = int(max(500, (len(audio_bytes) - 44) / 32))

        user_turn = ConversationTurn(
            session_id=conv_session.id,
            sequence=user_turn_seq,
            speaker="user",
            transcript=user_text,
            client_turn_id=client_turn_id,
            stt_provider=stt_provider_name,
            stt_model=stt_model_name,
            processing_time_ms=stt_ms,
            metrics={"stt_ms": stt_ms, "speech_duration_ms": speech_duration_ms, "confidence": stt_confidence},
            started_at=user_turn_start_time,
            ended_at=datetime.now(timezone.utc),
        )
        self.session.add(user_turn)
        await self.session.flush()

        # 3. Build AI Context & Query AI Router
        ai_start = time.perf_counter()

        learner_ctx_budget = await self.memory_retriever.retrieve_context(
            user_id=resolved_user_id,
            persona_role=conv_session.persona.role if conv_session.persona else None,
            max_items=4,
        )

        ai_request = self.context_manager.create_request(
            session=conv_session,
            persona=conv_session.persona,
            current_user_text=user_text,
            turns_history=conv_session.turns,
            user_id=resolved_user_id,
            learner_context=learner_ctx_budget.compact_prompt_block,
        )

        ai_response: AIResponse = await self.ai_router.generate(
            task=AITask.CONVERSATION,
            request=ai_request,
            user_id=resolved_user_id,
        )
        ai_ms = int((time.perf_counter() - ai_start) * 1000)

        # 4. Parse AI Output & Feedback Hint
        raw_ai_text = ai_response.text.strip()
        spoken_text = raw_ai_text
        feedback_hint = None

        if "---HINT---" in raw_ai_text:
            parts = raw_ai_text.split("---HINT---")
            spoken_text = parts[0].strip()
            feedback_hint = parts[1].strip()

        # 5. Synthesize Speech (TTS via unified TTSService with cache)
        tts_start = time.perf_counter()
        audio_base64 = None
        tts_error_msg = None
        tts_ms = 0
        tts_provider_used = (conv_session.tts_provider_preference or "voicevox").lower().strip()

        if tts_provider_used not in ("none", "off", "disabled", "web_speech"):
            try:
                tts_req = TTSRequest(
                    text=spoken_text,
                    provider=tts_provider_used,
                    voice_id=conv_session.tts_voice_preference or "1",
                    user_id=conv_session.user_id,
                    allow_fallback=True,
                )
                tts_output = await tts_service.synthesize(tts_req)
                tts_ms = tts_output.processing_time_ms or int((time.perf_counter() - tts_start) * 1000)
                if tts_output.audio_bytes:
                    audio_base64 = tts_output.audio_base64 or base64.b64encode(tts_output.audio_bytes).decode("utf-8")
            except SpeechError as se:
                logger.warning(f"[Conversation] TTS Synthesis failed for turn: {se}. Proceeding with text only.")
                tts_error_msg = se.message
                tts_ms = int((time.perf_counter() - tts_start) * 1000)
            except Exception as e:
                logger.warning(f"[Conversation] Unexpected TTS error: {e}. Proceeding with text only.")
                tts_error_msg = str(e)
                tts_ms = int((time.perf_counter() - tts_start) * 1000)

        total_turn_ms = int((time.perf_counter() - total_turn_start) * 1000)

        # 6. Persist Assistant Turn
        assistant_turn_seq = user_turn_seq + 1
        timings_breakdown = {
            "stt_ms": stt_ms,
            "ai_ms": ai_ms,
            "tts_ms": tts_ms,
            "total_ms": total_turn_ms,
        }

        assistant_turn = ConversationTurn(
            session_id=conv_session.id,
            sequence=assistant_turn_seq,
            speaker="assistant",
            transcript=spoken_text,
            client_turn_id=client_turn_id,
            ai_provider=ai_response.provider,
            ai_model=ai_response.model,
            tts_provider=tts_provider_used,
            tts_voice=conv_session.tts_voice_preference,
            processing_time_ms=total_turn_ms,
            metrics=timings_breakdown,
            feedback_hint=feedback_hint,
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc),
        )
        self.session.add(assistant_turn)
        await self.session.commit()

        await self.session.refresh(user_turn)
        await self.session.refresh(assistant_turn)

        # Asynchronously enqueue deep intelligence analysis for user turn
        try:
            await self.intelligence_service.enqueue_turn_analysis(session_id, user_turn.id)
        except Exception as ie:
            logger.warning(f"[Conversation] Background turn analysis enqueue failed: {ie}")

        # Asynchronously enqueue background pronunciation analysis based on sampling policy
        try:
            from app.domains.pronunciation.contracts import PronunciationAnalysisPolicy
            from app.domains.pronunciation.models import PronunciationAttempt
            from app.domains.pronunciation.queue import pronunciation_job_queue
            from app.domains.pronunciation.sampling_policy import PronunciationSamplingPolicy

            policy = PronunciationSamplingPolicy.determine_policy(
                session_mode=conv_session.mode,
                turn_sequence=user_turn.sequence,
            )
            if policy != PronunciationAnalysisPolicy.OFF:
                p_attempt_id = f"pron_{user_turn.id}"
                p_attempt = PronunciationAttempt(
                    id=p_attempt_id,
                    user_id=resolved_user_id,
                    session_id=conv_session.id,
                    turn_id=user_turn.id,
                    reference_text=user_turn.transcript,
                    target_type="conversation_line",
                    reference_type="synthetic",
                    analysis_status="pending",
                )
                self.session.add(p_attempt)
                await self.session.commit()

                import os
                import tempfile

                # Persist audio to temporary file for background worker to prevent queue memory ballooning
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
                    tmp_audio.write(audio_bytes)
                    tmp_audio_path = tmp_audio.name

                job_payload = {
                    "attempt_id": p_attempt_id,
                    "user_id": resolved_user_id,
                    "target_text": user_turn.transcript,
                    "expected_reading": None,
                    "target_type": "conversation_line",
                    "reference_type": "synthetic",
                    "session_id": conv_session.id,
                    "turn_id": user_turn.id,
                    "audio_path": tmp_audio_path,
                }
                await pronunciation_job_queue.enqueue(job_payload)
        except Exception as pe:
            logger.warning(f"[Conversation] Background pronunciation analysis enqueue skipped/failed: {pe}")

        return AudioTurnResponse(
            session_id=session_id,
            user_turn=ConversationTurnRead.model_validate(user_turn),
            assistant_turn=ConversationTurnRead.model_validate(assistant_turn),
            audio_base64=audio_base64,
            audio_format="wav",
            metrics=timings_breakdown,
            tts_error=tts_error_msg,
        )

    async def process_text_turn(
        self,
        session_id: str,
        user_text: str,
        client_turn_id: str | None = None,
        user_id: str | None = None,
    ) -> AudioTurnResponse:
        """Text-based turn execution (useful for text practice or testing)."""
        conv_session = await self._get_session_with_turns_or_404(session_id)
        if conv_session.status != "active":
            raise ValidationException(f"Cannot add turn to inactive session (status: {conv_session.status})")

        resolved_user_id = user_id or conv_session.user_id
        total_turn_start = time.perf_counter()

        # 1. Record User Turn
        current_max_seq = max([t.sequence for t in conv_session.turns], default=0)
        user_turn_seq = current_max_seq + 1

        user_turn = ConversationTurn(
            session_id=conv_session.id,
            sequence=user_turn_seq,
            speaker="user",
            transcript=user_text.strip(),
            client_turn_id=client_turn_id,
            processing_time_ms=0,
            metrics={"mode": "text_input"},
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc),
        )
        self.session.add(user_turn)
        await self.session.flush()

        # 2. Query AI Router
        ai_start = time.perf_counter()

        learner_ctx_budget = await self.memory_retriever.retrieve_context(
            user_id=resolved_user_id,
            persona_role=conv_session.persona.role if conv_session.persona else None,
            max_items=4,
        )

        ai_request = self.context_manager.create_request(
            session=conv_session,
            persona=conv_session.persona,
            current_user_text=user_text,
            turns_history=conv_session.turns,
            user_id=resolved_user_id,
            learner_context=learner_ctx_budget.compact_prompt_block,
        )

        ai_response: AIResponse = await self.ai_router.generate(
            task=AITask.CONVERSATION,
            request=ai_request,
            user_id=resolved_user_id,
        )
        ai_ms = int((time.perf_counter() - ai_start) * 1000)

        # 3. Parse text and hint
        raw_ai_text = ai_response.text.strip()
        spoken_text = raw_ai_text
        feedback_hint = None

        if "---HINT---" in raw_ai_text:
            parts = raw_ai_text.split("---HINT---")
            spoken_text = parts[0].strip()
            feedback_hint = parts[1].strip()

        # 4. Synthesize TTS via unified TTSService
        tts_start = time.perf_counter()
        audio_base64 = None
        tts_error_msg = None
        tts_ms = 0
        tts_provider_used = (conv_session.tts_provider_preference or "voicevox").lower().strip()

        if tts_provider_used not in ("none", "off", "disabled", "web_speech"):
            try:
                tts_req = TTSRequest(
                    text=spoken_text,
                    provider=tts_provider_used,
                    voice_id=conv_session.tts_voice_preference or "1",
                    user_id=conv_session.user_id,
                    allow_fallback=True,
                )
                tts_output = await tts_service.synthesize(tts_req)
                tts_ms = tts_output.processing_time_ms or int((time.perf_counter() - tts_start) * 1000)
                if tts_output.audio_bytes:
                    audio_base64 = tts_output.audio_base64 or base64.b64encode(tts_output.audio_bytes).decode("utf-8")
            except Exception as e:
                tts_error_msg = str(e)
                tts_ms = int((time.perf_counter() - tts_start) * 1000)

        total_turn_ms = int((time.perf_counter() - total_turn_start) * 1000)

        # 5. Persist Assistant Turn
        assistant_turn = ConversationTurn(
            session_id=conv_session.id,
            sequence=user_turn_seq + 1,
            speaker="assistant",
            transcript=spoken_text,
            client_turn_id=client_turn_id,
            ai_provider=ai_response.provider,
            ai_model=ai_response.model,
            tts_provider=conv_session.tts_provider_preference or "voicevox",
            tts_voice=conv_session.tts_voice_preference,
            processing_time_ms=total_turn_ms,
            metrics={"ai_ms": ai_ms, "tts_ms": tts_ms, "total_ms": total_turn_ms},
            feedback_hint=feedback_hint,
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc),
        )
        self.session.add(assistant_turn)
        await self.session.commit()

        await self.session.refresh(user_turn)
        await self.session.refresh(assistant_turn)

        # Asynchronously enqueue deep intelligence analysis for text turn
        try:
            await self.intelligence_service.enqueue_turn_analysis(session_id, user_turn.id)
        except Exception as ie:
            logger.warning(f"[Conversation] Background text turn analysis enqueue failed: {ie}")

        return AudioTurnResponse(
            session_id=session_id,
            user_turn=ConversationTurnRead.model_validate(user_turn),
            assistant_turn=ConversationTurnRead.model_validate(assistant_turn),
            audio_base64=audio_base64,
            audio_format="wav",
            metrics={"ai_ms": ai_ms, "tts_ms": tts_ms, "total_ms": total_turn_ms},
            tts_error=tts_error_msg,
        )

    @staticmethod
    def _to_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    async def end_session(self, session_id: str) -> ConversationSessionRead:
        """Concludes an active session and calculates total elapsed duration."""
        conv_session = await self._get_session_with_turns_or_404(session_id)
        if conv_session.status == "active":
            conv_session.status = "completed"
            now_utc = datetime.now(timezone.utc)
            conv_session.ended_at = now_utc
            started_at = self._to_utc(conv_session.started_at)
            duration_sec = int((now_utc - started_at).total_seconds()) if started_at else 0
            conv_session.duration_seconds = max(1, duration_sec)
            await self.session.commit()
            logger.info(f"[Conversation] Ended session '{session_id}' (duration: {conv_session.duration_seconds}s)")

            # Asynchronously enqueue session-level intelligence analysis
            try:
                await self.intelligence_service.enqueue_session_analysis(session_id)
            except Exception as ie:
                logger.warning(f"[Conversation] Background session analysis enqueue failed: {ie}")

            # Emit GameEvent to Gamification Engine
            try:
                from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
                from app.domains.gamification.infrastructure.game_event_publisher import GameEventPublisher

                user_turns_cnt = len([t for t in conv_session.turns if t.speaker == "user"])
                if user_turns_cnt > 0:
                    await GameEventPublisher.publish(
                        user_id=conv_session.user_id,
                        event_type=GameEventType.CONVERSATION_COMPLETED,
                        source=GameEventSource.CONVERSATION,
                        source_id=conv_session.id,
                        metadata={
                            "session_id": conv_session.id,
                            "duration_seconds": conv_session.duration_seconds,
                            "user_turns_count": user_turns_cnt,
                            "mode": conv_session.mode,
                        },
                    )
            except Exception as ge:
                logger.warning(f"[Conversation] Error emitting conversation.completed game event: {ge}")

        return await self.get_session(session_id)

    async def get_session_summary(self, session_id: str) -> ConversationSessionSummary:
        """Calculates speaking metrics and summary for a session."""
        conv_session = await self._get_session_with_turns_or_404(session_id)

        user_turns = [t for t in conv_session.turns if t.speaker == "user"]
        assistant_turns = [t for t in conv_session.turns if t.speaker == "assistant"]

        total_speaking_time = 0.0
        for t in user_turns:
            if t.metrics and "speech_duration_ms" in t.metrics:
                dur = t.metrics["speech_duration_ms"]
                if dur:
                    total_speaking_time += dur / 1000.0

        latencies = [
            t.processing_time_ms for t in assistant_turns if t.processing_time_ms is not None
        ]
        avg_latency = float(sum(latencies) / len(latencies)) if latencies else 0.0

        primary_ai = assistant_turns[-1].ai_provider if assistant_turns else conv_session.provider_preference
        primary_model = assistant_turns[-1].ai_model if assistant_turns else conv_session.model_preference

        duration_sec = conv_session.duration_seconds
        if duration_sec is None:
            started_at = self._to_utc(conv_session.started_at)
            end_time = self._to_utc(conv_session.ended_at) or datetime.now(timezone.utc)
            duration_sec = max(1, int((end_time - started_at).total_seconds())) if started_at else 1

        return ConversationSessionSummary(
            session_id=conv_session.id,
            persona_id=conv_session.persona_id,
            persona_name=conv_session.persona.name if conv_session.persona else "Unknown",
            mode=conv_session.mode,
            status=conv_session.status,
            started_at=conv_session.started_at,
            ended_at=conv_session.ended_at,
            duration_seconds=duration_sec,
            turn_count=len(conv_session.turns),
            user_turns_count=len(user_turns),
            assistant_turns_count=len(assistant_turns),
            total_speaking_time_seconds=round(total_speaking_time, 2),
            avg_turn_latency_ms=round(avg_latency, 1),
            primary_ai_provider=primary_ai,
            primary_ai_model=primary_model,
        )

    async def list_recent_sessions(
        self,
        user_id: str | None = None,
        limit: int = 5,
    ) -> list[ConversationRecentSessionRead]:
        """Queries recent conversation sessions with persona and turn metadata."""
        resolved_user_id = user_id or (await self.user_service.get_or_create_default_user()).id
        stmt = (
            select(ConversationSession)
            .where(ConversationSession.user_id == resolved_user_id)
            .options(
                selectinload(ConversationSession.persona),
                selectinload(ConversationSession.turns),
            )
            .order_by(ConversationSession.started_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        sessions = res.scalars().all()

        recent_list: list[ConversationRecentSessionRead] = []
        for s in sessions:
            started_at = self._to_utc(s.started_at)
            end_time = self._to_utc(s.ended_at) or (datetime.now(timezone.utc) if s.status == "active" else started_at)
            dur = s.duration_seconds or (max(1, int((end_time - started_at).total_seconds())) if started_at else 0)

            turn_count = len(s.turns)
            score = min(98, max(72, 78 + turn_count * 2)) if turn_count > 0 else None

            topic = s.persona.role if s.persona else "Luyện nói tự do"
            if s.turns and len(s.turns) > 0:
                first_transcript = s.turns[0].transcript
                if first_transcript and len(first_transcript) > 5:
                    topic = first_transcript[:45] + "..." if len(first_transcript) > 45 else first_transcript

            recent_list.append(
                ConversationRecentSessionRead(
                    id=s.id,
                    persona_id=s.persona_id,
                    persona_name=s.persona.name if s.persona else "Unknown",
                    persona_avatar_url=s.persona.avatar_url if s.persona else None,
                    mode=s.mode,
                    status=s.status,
                    started_at=s.started_at,
                    ended_at=s.ended_at,
                    duration_seconds=dur,
                    turns_count=turn_count,
                    score=score,
                    topic=topic,
                )
            )

        return recent_list
