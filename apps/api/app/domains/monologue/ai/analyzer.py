"""AI semantic analysis for monologue — coherence, relevance, naturalness, genre_fit, native upgrade."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.monologue.ai.prompts import MonologuePrompts
from app.domains.monologue.contracts import SpeechGenre


class MonologueAIAnalyzer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.router = AIRouter(db)

    async def evaluate(
        self,
        user_id: str,
        genre: SpeechGenre | str,
        topic: str,
        instruction: str,
        constraints: list[str],
        transcript: str,
        deterministic: dict[str, Any],
        duration_sec: int,
    ) -> dict[str, Any] | None:
        if not transcript or len(transcript.strip()) < 5:
            return None
        # Normalize genre
        if isinstance(genre, str):
            try:
                genre_e = SpeechGenre(genre.lower())
            except Exception:
                genre_e = SpeechGenre.OPINION
        else:
            genre_e = genre

        sys_inst, user_content = MonologuePrompts.build_evaluation_prompt(
            genre=genre_e, topic=topic, instruction=instruction, constraints=constraints,
            transcript=transcript, deterministic_context=deterministic, duration_sec=duration_sec
        )
        # Use SPEECH_EVALUATION task
        task = getattr(AITask, "SPEECH_EVALUATION", AITask.GENERAL)
        req = AIRequest(
            task=task,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.3,
            max_output_tokens=800,
            user_id=user_id,
        )
        try:
            resp = await self.router.generate(task=task, request=req, user_id=user_id)
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt.replace("```json", "", 1).rstrip("```").strip()
            elif txt.startswith("```"):
                txt = txt.replace("```", "", 1).rstrip("```").strip()
            parsed = json.loads(txt)
            # sanitize + clamp
            for k in ("relevance", "coherence", "naturalness", "genre_fit", "argument_quality", "content_score"):
                if k in parsed and parsed[k] is not None:
                    try:
                        parsed[k] = max(0, min(100, float(parsed[k])))
                    except Exception:
                        pass
            if "confidence" in parsed:
                try:
                    c = float(parsed["confidence"])
                    if c > 1:
                        c = c / 100 if c <= 100 else 1.0
                    parsed["confidence"] = max(0, min(1, c))
                except Exception:
                    parsed["confidence"] = 0.85
            # ensure feedback list
            if "feedback" in parsed and isinstance(parsed["feedback"], str):
                parsed["feedback"] = [parsed["feedback"]]
            parsed["_provider"] = resp.provider
            parsed["_model"] = resp.model
            return parsed
        except Exception as e:
            logger.warning(f"[MonologueAI] evaluate failed: {e}", exc_info=True)
            raise  # propagate for hard error handling — caller will surface via toast

    async def native_upgrade(
        self,
        user_id: str,
        transcript: str,
        genre: SpeechGenre | str,
        topic: str,
        level: str = "N3",
    ) -> dict[str, Any] | None:
        if not transcript or len(transcript.strip()) < 5:
            return None
        if isinstance(genre, str):
            try:
                genre_e = SpeechGenre(genre.lower())
            except Exception:
                genre_e = SpeechGenre.OPINION
        else:
            genre_e = genre
        sys_inst, user_content = MonologuePrompts.build_native_upgrade_prompt(transcript, genre_e, topic, level)
        task = getattr(AITask, "SPEECH_NATIVE_UPGRADE", AITask.GENERAL)
        req = AIRequest(
            task=task,
            system_instruction=sys_inst,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.4,
            max_output_tokens=900,
            user_id=user_id,
        )
        try:
            resp = await self.router.generate(task=task, request=req, user_id=user_id)
            txt = resp.text.strip()
            if txt.startswith("```json"):
                txt = txt.replace("```json", "", 1).rstrip("```").strip()
            elif txt.startswith("```"):
                txt = txt.replace("```", "", 1).rstrip("```").strip()
            parsed = json.loads(txt)
            # never invent claims check: ensure minimal_correction not drastically longer than transcript with new facts
            # sanitized here minimally; evaluator will preserve
            parsed["_provider"] = resp.provider
            parsed["_model"] = resp.model
            return parsed
        except Exception as e:
            logger.warning(f"[MonologueAI] native_upgrade failed: {e}", exc_info=True)
            raise
