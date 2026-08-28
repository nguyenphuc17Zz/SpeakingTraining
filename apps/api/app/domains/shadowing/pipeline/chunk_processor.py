import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
from app.domains.ai.router import AIRouter
from app.domains.shadowing.contracts import TranscriptSegmentDTO
from app.domains.shadowing.prompts import ShadowingPrompts


class ChunkProcessor:
    """Processes large YouTube transcripts in safe, token-bounded chunks to avoid AI cost and context bloat."""

    CHUNK_SIZE = 15  # Segments per AI chunk

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.ai_router = AIRouter(db_session)

    async def process_transcript_chunks(
        self,
        segments: list[TranscriptSegmentDTO],
        user_id: str,
        learner_goals: list[str] | None = None,
        learner_weaknesses: list[str] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Executes chunked AI analysis for vocabulary, grammar, and natural expressions.
        Returns aggregate dictionaries of extracted items.
        """
        all_vocab: list[dict[str, Any]] = []
        all_grammar: list[dict[str, Any]] = []
        all_expressions: list[dict[str, Any]] = []

        if not segments:
            return {"vocabulary": [], "grammar": [], "expressions": []}

        # Process top/first few chunks (max 3 chunks = ~45 segments to keep analysis fast and responsive)
        num_chunks = min(3, (len(segments) + self.CHUNK_SIZE - 1) // self.CHUNK_SIZE)

        for chunk_idx in range(num_chunks):
            start_i = chunk_idx * self.CHUNK_SIZE
            end_i = min(len(segments), start_i + self.CHUNK_SIZE)
            chunk_segs = [
                {
                    "id": s.id,
                    "normalized_text": s.normalized_text,
                    "text": s.text,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                }
                for s in segments[start_i:end_i]
            ]

            sys_inst, user_content = ShadowingPrompts.build_chunk_analysis_prompt(
                chunk_segments=chunk_segs,
                learner_goals=learner_goals,
                learner_weaknesses=learner_weaknesses,
            )

            req = AIRequest(
                task=AITask.SHADOWING_ANALYSIS,
                system_instruction=sys_inst,
                messages=[
                    AIMessage(role=AIMessageRole.SYSTEM, content=sys_inst),
                    AIMessage(role=AIMessageRole.USER, content=user_content),
                ],
                response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
                temperature=0.2,
                max_output_tokens=2048,
                user_id=user_id,
            )

            try:
                resp = await self.ai_router.generate(task=AITask.SHADOWING_ANALYSIS, request=req, user_id=user_id)
                clean_text = resp.text.strip()
                if "```json" in clean_text:
                    clean_text = clean_text.split("```json", 1)[1].split("```", 1)[0].strip()
                elif "```" in clean_text:
                    clean_text = clean_text.split("```", 1)[1].split("```", 1)[0].strip()

                parsed = json.loads(clean_text)
                all_vocab.extend(parsed.get("vocabulary", []))
                all_grammar.extend(parsed.get("grammar", []))
                all_expressions.extend(parsed.get("natural_expressions", []))
            except Exception as e:
                logger.warning(f"[ChunkProcessor] AI extraction error on chunk {chunk_idx}: {e}")

        return {
            "vocabulary": all_vocab,
            "grammar": all_grammar,
            "expressions": all_expressions,
        }
