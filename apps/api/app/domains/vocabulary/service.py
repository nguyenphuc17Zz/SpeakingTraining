from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
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
from app.domains.japanese.provider import get_language_provider
from app.domains.learner_memory.models import LearnerMemory
from app.domains.learning.contracts import LearningItemLifecycle
from app.domains.learning.models import LearningItem
from app.domains.vocabulary.schemas import (
    AlternativeItem,
    BestMatch,
    ExampleSentence,
    SaveVocabularyNotebookRequest,
    SaveVocabularyNotebookResponse,
    VocabularyLookupRequest,
    VocabularyLookupResponse,
)


def _clean_json_text(text: str) -> str:
    """Extract raw JSON string from potential markdown formatting."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


class VocabularyService:
    """Pedagogical Context-Aware AI Vocabulary Lookup & Notebook Service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.lang_provider = get_language_provider()

    async def lookup_contextual_vocabulary(
        self, payload: VocabularyLookupRequest, user_id: str
    ) -> VocabularyLookupResponse:
        """
        Performs in-depth context-aware vocabulary analysis using AI.
        Falls back to local morphological analysis (Sudachi) if AI fails.
        """
        query = payload.query.strip()
        context = (payload.context or "").strip()
        target_level = payload.target_level or "N3"
        register_pref = payload.register_preference or "auto"

        system_instruction = (
            "Bạn là một chuyên gia ngôn ngữ học tiếng Nhật, chuyên gia từ điển sư phạm Nhật - Việt "
            "và huấn luyện viên phản xạ giao tiếp tiếng Nhật chuyên sâu.\n"
            "Nhiệm vụ của bạn là phân tích từ vựng hoặc cụm từ được bôi đen THEO ĐÚNG NGỮ CẢNH CÂU VĂN THỰC TẾ được cung cấp.\n\n"
            "CÁC NGUYÊN TẮC BẮT BUỘC:\n"
            "1. Phải phân tích chính xác nghĩa và sắc thái của từ/cụm từ TRONG ĐÚNG CÂU VĂN ĐÓ, không đưa ra định nghĩa từ điển chung chung, rời rạc.\n"
            "2. Giải thích lý do vì sao từ này được dùng trong ngữ cảnh này (sắc thái tình cảm, thái độ, mức độ trang trọng/thân mật, thói quen bản xứ).\n"
            "3. Đưa ra 2 câu ví dụ thực tế kèm hoàn cảnh giao tiếp cụ thể (situation) và dịch nghĩa tiếng Việt tự nhiên.\n"
            "4. Đưa ra 2-3 từ thay thế / đồng nghĩa (alternatives) kèm phân tích sự khác biệt về sắc thái (difference_explanation) để người học biết khi nào nên dùng từ nào.\n"
            "5. Đảm bảo trả về JSON chuẩn xác theo đúng cấu trúc yêu cầu, không thêm chữ thừa ngoài JSON."
        )

        user_content = (
            f"Hãy phân tích từ vựng/cụm từ bôi đen sau đây:\n"
            f"- Từ/Cụm từ bôi đen: {query}\n"
            f"- Ngữ cảnh câu văn (Context): {context if context else '(Không có ngữ cảnh bổ sung, hãy phân tích theo các ngữ cảnh giao tiếp thông dụng nhất)'}\n"
            f"- Cấp độ người học: {target_level}\n"
            f"- Ưu tiên phong cách/sắc thái: {register_pref}\n\n"
            "Cấu trúc JSON bắt buộc:\n"
            "{\n"
            '  "best_match": {\n'
            '    "expression": "Chữ Hán/Dạng chuẩn của từ",\n'
            '    "reading": "Cách đọc Hiragana / Furigana",\n'
            '    "meaning_vi": "Nghĩa tiếng Việt chuẩn xác trong ngữ cảnh này",\n'
            '    "part_of_speech": "Từ loại (Danh từ, Động từ nhóm..., Tính từ..., Phó từ...)",\n'
            '    "jlpt_level": "N5/N4/N3/N2/N1",\n'
            '    "register": "Casual / Polite / Business Keigo",\n'
            '    "naturalness_score": 95,\n'
            '    "nuance_explanation": "Giải thích sư phạm sâu sắc: tại sao từ này phù hợp trong câu, mang sắc thái gì",\n'
            '    "usage_collocation": "Cụm từ đi kèm tự nhiên (Collocations)",\n'
            '    "examples": [\n'
            '      {"ja": "Câu ví dụ 1", "vi": "Dịch nghĩa 1", "situation": "Hoàn cảnh 1"},\n'
            '      {"ja": "Câu ví dụ 2", "vi": "Dịch nghĩa 2", "situation": "Hoàn cảnh 2"}\n'
            "    ]\n"
            "  },\n"
            '  "alternatives": [\n'
            '    {"expression": "Từ thay thế 1", "reading": "Cách đọc", "meaning_vi": "Nghĩa tiếng Việt", "difference_explanation": "Khác biệt sắc thái so với từ gốc"},\n'
            '    {"expression": "Từ thay thế 2", "reading": "Cách đọc", "meaning_vi": "Nghĩa tiếng Việt", "difference_explanation": "Khác biệt sắc thái so với từ gốc"}\n'
            "  ]\n"
            "}"
        )

        ai_req = AIRequest(
            task=AITask.VOCABULARY_LOOKUP,
            messages=[
                AIMessage(role=AIMessageRole.SYSTEM, content=system_instruction),
                AIMessage(role=AIMessageRole.USER, content=user_content),
            ],
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.3,
            max_output_tokens=1500,
        )

        try:
            res = await self.ai_router.generate(ai_req, user_id=user_id)
            cleaned_text = _clean_json_text(res.text)
            data = json.loads(cleaned_text)

            bm_raw = data.get("best_match", {})
            alts_raw = data.get("alternatives", [])

            examples = [
                ExampleSentence(
                    ja=ex.get("ja", ""),
                    vi=ex.get("vi", ""),
                    situation=ex.get("situation", ""),
                )
                for ex in bm_raw.get("examples", [])
                if ex.get("ja")
            ]

            # Ensure at least 2 examples if LLM returned fewer
            if len(examples) < 2:
                if not examples:
                    examples.append(
                        ExampleSentence(
                            ja=f"{query}について詳しく教えていただけますか。",
                            vi=f"Bạn có thể cho tôi biết chi tiết về {query} được không?",
                            situation="Khi trao đổi công việc hoặc hỏi thêm thông tin",
                        )
                    )
                examples.append(
                    ExampleSentence(
                        ja=f"実際に{query}を使ってみると、とても便利でした。",
                        vi=f"Khi thử dùng {query} trên thực tế, tôi thấy nó rất tiện lợi.",
                        situation="Khi chia sẻ trải nghiệm thực tế với bạn bè hoặc đồng nghiệp",
                    )
                )

            best_match = BestMatch(
                expression=bm_raw.get("expression") or query,
                reading=bm_raw.get("reading") or self._resolve_reading(query),
                meaning_vi=bm_raw.get("meaning_vi") or "Đang cập nhật nghĩa ngữ cảnh",
                part_of_speech=bm_raw.get("part_of_speech") or "Từ vựng",
                jlpt_level=bm_raw.get("jlpt_level") or target_level,
                register=bm_raw.get("register") or "Polite",
                naturalness_score=int(bm_raw.get("naturalness_score") or 95),
                nuance_explanation=bm_raw.get("nuance_explanation")
                or f"Từ 「{query}」 được dùng chuẩn xác và tự nhiên trong câu văn.",
                usage_collocation=bm_raw.get("usage_collocation") or "",
                examples=examples,
            )

            alternatives = [
                AlternativeItem(
                    expression=alt.get("expression", ""),
                    reading=alt.get("reading", ""),
                    meaning_vi=alt.get("meaning_vi", ""),
                    difference_explanation=alt.get("difference_explanation", ""),
                )
                for alt in alts_raw
                if alt.get("expression")
            ]

            return VocabularyLookupResponse(
                best_match=best_match,
                alternatives=alternatives,
                original_query=query,
                context=context,
                searched_at=datetime.now(timezone.utc).isoformat(),
            )

        except Exception as ex:
            logger.warning(
                f"[VocabularyService] AI lookup failed for query '{query}': {ex}. Falling back to linguistic heuristics."
            )
            return self._build_fallback_response(query, context, target_level)

    def _resolve_reading(self, text: str) -> str:
        """Resolve Kana reading using Sudachi analyzer."""
        try:
            tokens = self.lang_provider.analyze(text)
            readings = [t.reading or t.surface for t in tokens]
            return "".join(readings)
        except Exception:
            return text

    def _build_fallback_response(
        self, query: str, context: str, target_level: str
    ) -> VocabularyLookupResponse:
        """Deterministic linguistic fallback when LLM is unavailable."""
        reading = self._resolve_reading(query)
        pos = "Từ vựng tiếng Nhật"
        try:
            tokens = self.lang_provider.analyze(query)
            if tokens:
                pos = f"{tokens[0].pos} ({tokens[0].pos_detail or ''})".strip()
        except Exception:
            pass

        best_match = BestMatch(
            expression=query,
            reading=reading,
            meaning_vi=f"Từ vựng / Cụm từ: {query}",
            part_of_speech=pos,
            jlpt_level=target_level,
            register="Polite / Tự nhiên",
            naturalness_score=90,
            nuance_explanation=(
                f"Từ 「{query}」 xuất hiện trong ngữ cảnh: 「{context[:100]}...」. "
                f"Đây là cách diễn đạt phổ biến và chuẩn mực trong giao tiếp tiếng Nhật."
                if context
                else f"Từ 「{query}」 là từ vựng thông dụng trong tiếng Nhật giao tiếp."
            ),
            usage_collocation=f"〜{query}",
            examples=[
                ExampleSentence(
                    ja=f"{query}の使い方を確認しましょう。",
                    vi=f"Hãy cùng xác nhận cách sử dụng của {query}.",
                    situation="Khi học tập và luyện tập giao tiếp",
                ),
                ExampleSentence(
                    ja=f"日常会話で{query}がよく使われます。",
                    vi=f"Trong hội thoại thường ngày, {query} thường xuyên được sử dụng.",
                    situation="Giao tiếp tự nhiên hàng ngày",
                ),
            ],
        )

        return VocabularyLookupResponse(
            best_match=best_match,
            alternatives=[
                AlternativeItem(
                    expression=query,
                    reading=reading,
                    meaning_vi="Biến thể đồng nghĩa",
                    difference_explanation="Dạng tương đương trong các ngữ cảnh khác nhau.",
                )
            ],
            original_query=query,
            context=context,
            searched_at=datetime.now(timezone.utc).isoformat(),
        )

    async def save_to_notebook(
        self, payload: SaveVocabularyNotebookRequest, user_id: str
    ) -> SaveVocabularyNotebookResponse:
        """
        Saves the looked-up vocabulary word into LearnerMemory and active LearningItems catalog
        for personalized spaced repetition and review.
        """
        key = f"vocab:{payload.expression.strip()}"
        statement = f"{payload.expression} ({payload.reading}): {payload.meaning_vi}"

        # 1. Update or create LearnerMemory
        mem_stmt = select(LearnerMemory).where(
            LearnerMemory.user_id == user_id,
            LearnerMemory.key == key,
        )
        mem_res = await self.db.execute(mem_stmt)
        mem = mem_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if not mem:
            mem = LearnerMemory(
                user_id=user_id,
                memory_type="vocabulary",
                key=key,
                statement=statement,
                category=payload.part_of_speech or "vocabulary",
                evidence_count=1,
                confidence=0.9,
                severity="SHOULD_FIX",
                severity_score=40,
                priority_score=0.75,
                mastery=0.2,
                attempt_count=1,
                correct_count=1,
                error_count=0,
                first_seen=now,
                last_seen=now,
                trend="new",
                status="active",
                contexts_used=[payload.context] if payload.context else [],
            )
            self.db.add(mem)
        else:
            mem.statement = statement
            mem.last_seen = now
            mem.evidence_count += 1
            if payload.context:
                existing_contexts = mem.contexts_used or []
                if payload.context not in existing_contexts:
                    mem.contexts_used = existing_contexts + [payload.context]

        # 2. Create or update LearningItem in training catalog
        item_stmt = select(LearningItem).where(
            LearningItem.user_id == user_id,
            LearningItem.key == key,
        )
        item_res = await self.db.execute(item_stmt)
        item = item_res.scalar_one_or_none()

        if not item:
            item = LearningItem(
                user_id=user_id,
                memory_key=key,
                key=key,
                item_type="vocabulary",
                title=f"Từ vựng: {payload.expression} ({payload.reading})",
                description=f"{payload.meaning_vi}. {payload.nuance_explanation}",
                difficulty="normal",
                lifecycle=LearningItemLifecycle.ACTIVE.value,
                status="active",
                overall_mastery=0.2,
                recognition_mastery=0.3,
                production_mastery=0.1,
                spontaneous_mastery=0.0,
                context_variety_score=0.25,
                confidence=0.85,
                priority_score=0.8,
                attempt_count=1,
                success_count=1,
                independent_success_count=0,
                assisted_success_count=1,
                review_streak=1,
                review_interval_days=1,
                last_practiced_at=now,
                contexts_used=[payload.context] if payload.context else [],
                extra_metadata={
                    "expression": payload.expression,
                    "reading": payload.reading,
                    "meaning_vi": payload.meaning_vi,
                    "jlpt_level": payload.jlpt_level,
                    "register": payload.register,
                    "tags": payload.tags,
                },
            )
            self.db.add(item)
        else:
            item.title = f"Từ vựng: {payload.expression} ({payload.reading})"
            item.description = f"{payload.meaning_vi}. {payload.nuance_explanation}"
            item.last_practiced_at = now
            if payload.context:
                existing_ctxs = item.contexts_used or []
                if payload.context not in existing_ctxs:
                    item.contexts_used = existing_ctxs + [payload.context]

        await self.db.commit()
        await self.db.refresh(item)

        logger.info(
            f"[VocabularyService] Saved vocabulary '{payload.expression}' to notebook & learning items for user '{user_id}'"
        )
        return SaveVocabularyNotebookResponse(
            success=True,
            item_id=item.id,
            message=f"Đã lưu từ 「{payload.expression}」 vào Sổ tay từ vựng & Lộ trình học thành công!",
            created_at=now.isoformat(),
        )
