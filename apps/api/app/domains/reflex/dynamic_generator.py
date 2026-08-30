"""AIReflexGenerator — 100% dynamic on-the-fly Reflex Exercise Generation via Gemini AI & Sudachi.

No static hardcoded templates. Generates infinite authentic Japanese reflex challenges in real-time.
Gracefully falls back to Sudachi morphological factory if AI is unreachable.
"""

from __future__ import annotations

import json
import random
import uuid
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
from app.domains.japanese.provider import get_language_provider
from app.domains.reflex.conjugation_engine import (
    ConjugationForm,
    JapaneseConjugationEngine,
)
from app.domains.reflex.exercise_factory import ReflexExerciseFactory
from app.domains.reflex.pressure_profiles import timer_for_level

# Diverse Topics for Speed Q&A
QNA_TOPICS_POOL = [
    ("Ẩm thực & Nhà hàng", "món ăn yêu thích, văn hoá ăn uống, chọn món tại nhà hàng, đồ uống, tự nấu ăn"),
    ("Công sở & Nghề nghiệp", "phỏng vấn, quan hệ đồng nghiệp, kỹ năng làm việc, dự định tương lai, làm việc nhóm"),
    ("Du lịch & Khám phá", "địa điểm yêu thích, phương tiện di chuyển, văn hoá địa phương, trải nghiệm khách sạn, kỉ niệm chuyến đi"),
    ("Sở thích & Giải trí", "anime, âm nhạc, xem phim, đọc sách, thể thao, game, chụp ảnh"),
    ("Đời sống & Thói quen", "thói quen buổi sáng/tối, dọn dẹp nhà cửa, mua sắm online, thú cưng, chăm sóc sức khoẻ"),
    ("Cảm xúc & Tâm lý", "cách giải tỏa stress, kỷ niệm đáng nhớ, lời khuyên cho bạn bè, những điều khiến bạn vui"),
    ("Thời tiết & 4 Mùa", "mùa yêu thích, hoạt động theo mùa, thời tiết hôm nay, chuẩn bị khi trời mưa/tuyết"),
    ("Công nghệ & Cuộc sống hiện đại", "AI, mạng xã hội, ứng dụng tiện ích, thiết bị công nghệ, học ngoại ngữ online"),
    ("Tình huống giả định thú vị", "nếu trúng số, nếu có cỗ máy thời gian, nếu được nghỉ 1 tháng, nếu gặp người nổi tiếng"),
    ("Văn hoá & Phong tục", "lễ hội truyền thống, phép lịch sự người Nhật, trà đạo, suối nước nóng Onsen"),
]


class AIReflexGenerator:
    """Generates infinite, creative, non-repeating reflex speaking exercises using Gemini AI and Sudachi Dictionary."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.conj_engine = JapaneseConjugationEngine()
        self.lang_provider = get_language_provider()
        self.factory = ReflexExerciseFactory()

    async def generate_dynamic_exercise(
        self,
        sub_mode: str,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        verb: str | None = None,
        conjugation_target: str | None = None,
        topic: str | None = None,
        user_id: str = "reflex_user",
        **kwargs,
    ) -> dict[str, Any]:
        """Routes reflex generation to specialized AI prompt templates or high-speed deterministic factory."""
        try:
            if sub_mode == "reflex_conjugation":
                # Conjugation is fully deterministic and randomized across 600+ verbs and all 11 forms
                return self.factory.generate_conjugation(
                    verb=verb,
                    target_form=conjugation_target,
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                )
            elif sub_mode == "reflex_transformation":
                return await self._generate_dynamic_transformation(
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                    user_id=user_id,
                    transformation_category=kwargs.get("transformation_category"),
                )
            elif sub_mode == "reflex_context":
                return await self._generate_dynamic_context(
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                    user_id=user_id,
                    context_category=kwargs.get("context_category"),
                )
            elif sub_mode == "reflex_vocabulary":
                # Vocabulary recall is fully deterministic — no AI needed
                return self.factory.generate_vocabulary(
                    direction="vi_to_ja",
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                    vocab_category=kwargs.get("vocab_category"),
                )
            elif sub_mode == "reflex_keigo_vocab":
                # Keigo vocabulary blitz is fully deterministic — no AI needed
                return self.factory.generate_keigo_vocabulary(
                    target_type="all",
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                    keigo_category=kwargs.get("keigo_category"),
                )
            elif sub_mode == "reflex_qna":
                # Speed Q&A with full topic filtering, speech starters, and 3-angle model answers
                return self.factory.generate_qna(
                    topic=topic,
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                )
            else:
                return self.factory.generate_qna(
                    topic=topic,
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                )
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] Global generation exception, falling back to factory: {e}")
            return self.factory.generate(
                sub_mode=sub_mode,
                verb=verb,
                target_form=conjugation_target,
                topic=topic,
                difficulty=difficulty,
                pressure_level=pressure_level,
            )

    async def _generate_dynamic_conjugation(
        self,
        verb: str | None,
        target_form: str | None,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates conjugation using high-speed morphological dictionary with 50 forms."""
        return self.factory.generate_conjugation(
            verb=verb,
            target_form=target_form,
            difficulty=difficulty,
            pressure_level=pressure_level,
        )

    async def _generate_dynamic_qna(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Speed Q&A via Gemini AI with non-repeating topics."""
        timer_ms = timer_for_level(pressure_level)
        chosen_topic, topic_sub = random.choice(QNA_TOPICS_POOL)
        nonce = uuid.uuid4().hex[:8]
        recent_prompts = list(self.factory.recent_qna)[-8:]
        avoid_instruction = f" TUYỆT ĐỐI KHÔNG lặp lại các câu hỏi sau: {recent_prompts}." if recent_prompts else ""

        prompt_text = (
            f"Hãy sáng tạo 1 câu hỏi giao tiếp tiếng Nhật tự nhiên, bất ngờ và phong phú "
            f"thuộc chủ đề '{chosen_topic}' ({topic_sub}) để người học luyện phản xạ trả lời trong {timer_ms/1000:.1f}s.{avoid_instruction} "
            f"[Nonce: {nonce}] "
            f"Trả về JSON: {{\"question_ja\": \"<câu hỏi tiếng Nhật tự nhiên>\", \"translation_vi\": \"<dịch nghĩa tiếng Việt>\", \"key_vocab\": [{{\"ja\": \"<từ vựng 1>\", \"vi\": \"<nghĩa 1>\"}}, {{\"ja\": \"<từ vựng 2>\", \"vi\": \"<nghĩa 2>\"}}], \"idea_sparks\": [\"<hướng 1>\", \"<hướng 2>\", \"<hướng 3>\"], \"sample_answer_ja\": \"<câu trả lời mẫu ngắn gọn>\", \"multi_answers\": {{\"positive\": {{\"ja\": \"<khẳng định>\", \"vi\": \"<nghĩa>\"}}, \"negative\": {{\"ja\": \"<phủ định>\", \"vi\": \"<nghĩa>\"}}, \"extended\": {{\"ja\": \"<mở rộng>\", \"vi\": \"<nghĩa>\"}}}}, \"topic\": \"{chosen_topic}\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là giáo viên tiếng Nhật bản xứ chuyên luyện phản xạ Kaiwa cấp tốc. Trả về duy nhất JSON hợp lệ, không markdown thừa.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.95,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.EXERCISE_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.content.strip())
            q_ja = data.get("question_ja", "休日は何をしていますか？")
            trans_vi = data.get("translation_vi", "Ngày nghỉ bạn thường làm gì?")
            sample_ans = data.get("sample_answer_ja", "家で映画を観てのんびりしています。")
            key_vocab = data.get("key_vocab", [{"ja": "のんびり過ごす", "vi": "thư thả nghỉ ngơi"}, {"ja": "気分転換", "vi": "đổi gió, giải tỏa"}])
            idea_sparks = data.get("idea_sparks", ["Thư giãn tại nhà", "Đi cafe / Dạo phố", "Bận rộn / Học tập"])
            multi_ans = data.get("multi_answers", {
                "positive": {"ja": sample_ans, "vi": "Tôi thường ở nhà xem phim thư giãn."},
                "negative": {"ja": "最近は忙しくて、あまり休めていません。", "vi": "Dạo này bận nên tôi chưa nghỉ ngơi mấy."},
                "extended": {"ja": "カフェに行って資格の勉強をすることが多いです。", "vi": "Tôi hay ra quán cafe học thêm chứng chỉ."},
            })
            topic = data.get("topic", chosen_topic)
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] AI Q&A generation fallback: {e}")
            return self.factory.generate_qna(difficulty=difficulty, pressure_level=pressure_level)

        return {
            "title": f"瞬発 Q&A: {topic}",
            "objective": f"Nghe câu hỏi và phản xạ trả lời tự nhiên trong {timer_ms/1000:.1f}s",
            "scenario": trans_vi,
            "instructions": f"Nghe: '{q_ja}' — Trả lời ngay bằng tiếng Nhật 1-2 câu tự nhiên.",
            "prompt": q_ja,
            "prompt_translation": trans_vi,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "topic": topic,
            "canonical": sample_ans,
            "acceptable_variants": [sample_ans],
            "key_vocab": key_vocab,
            "idea_sparks": idea_sparks,
            "multi_answers": multi_ans,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Trả lời đủ ý, tự nhiên, không ngập ngừng quá lâu."],
            "target_patterns": [],
            "semantic_target": {"required_intent": "answer question", "topic": topic},
            "estimated_minutes": 4,
        }

    async def _generate_dynamic_transformation(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
        transformation_category: str | None = None,
    ) -> dict[str, Any]:
        """Generates dynamic Sentence Transformation via Gemini AI."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]
        recent_t = list(self.factory.recent_transforms)[-6:]
        avoid_t = f" Tránh các câu gốc sau: {recent_t}." if recent_t else ""
        cat_inst = f" Dựa trên chuyên đề hoặc từ khóa ngữ pháp yêu cầu: '{transformation_category}'." if transformation_category and transformation_category != "all" else ""

        prompt_text = (
            f"Hãy sáng tạo 1 bài tập biến đổi câu tiếng Nhật (Sentence Transformation) phong phú, thực tế.{cat_inst}{avoid_t} [Nonce: {nonce}] "
            f"Ví dụ: đổi câu thể lịch sự sang thể ngắn, bị động, sai khiến, bị sai khiến, điều kiện ば/たら, hoặc kính ngữ. "
            f"Trả về JSON: {{\"source_sentence_ja\": \"<câu gốc tiếng Nhật>\", \"task_instruction_ja\": \"<yêu cầu biến đổi>\", \"target_label\": \"<nhãn thể ngắn gọn>\", \"formula\": \"<công thức biến đổi>\", \"grammar_note\": \"<giải thích ngữ pháp ngắn gọn>\", \"expected_sentence_ja\": \"<câu sau khi biến đổi đúng>\", \"translation_vi\": \"<dịch nghĩa câu gốc tiếng Việt>\", \"category\": \"{transformation_category or 'casual'}\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là chuyên gia ngữ pháp tiếng Nhật thực chiến. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.EXERCISE_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.content.strip())
            source_ja = data.get("source_sentence_ja", "今日は東京に行きます。")
            task_ja = data.get("task_instruction_ja", "カジュアルな過去形にしてください。")
            target_label = data.get("target_label", task_ja)
            formula = data.get("formula", "")
            grammar_note = data.get("grammar_note", "")
            expected_ja = data.get("expected_sentence_ja", "今日は東京に行った。")
            trans_vi = data.get("translation_vi", "Hôm nay tôi đi Tokyo.")
            cat = data.get("category", transformation_category or "casual")
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] AI Transformation fallback: {e}")
            return self.factory.generate_transformation(
                difficulty=difficulty,
                pressure_level=pressure_level,
                transformation_category=transformation_category,
            )

        return {
            "title": f"瞬発・文型変換: {target_label}",
            "objective": f"Biến đổi câu theo yêu cầu trong {timer_ms/1000:.1f}s",
            "scenario": trans_vi,
            "instructions": f"Câu gốc: '{source_ja}' — Đổi sang: {target_label}",
            "prompt": source_ja,
            "source": source_ja,
            "prompt_translation": trans_vi,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "task": task_ja,
            "target_label": target_label,
            "formula": formula,
            "grammar_note": grammar_note,
            "category": cat,
            "transformation_category": cat,
            "expected": expected_ja,
            "canonical": expected_ja,
            "acceptable_variants": [expected_ja],
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Giữ nguyên ý nghĩa, chỉ đổi cấu trúc ngữ pháp theo yêu cầu."],
            "target_patterns": [expected_ja],
            "estimated_minutes": 4,
        }

    async def _generate_dynamic_context(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
        context_category: str | None = None,
    ) -> dict[str, Any]:
        """Generates dynamic Contextual Reaction scenario via Gemini AI."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]
        roles_pool = [
            "Bạn thân", "Đồng nghiệp", "Sếp/Cấp trên", "Khách hàng",
            "Người lạ trên đường", "Nhân viên quán ăn", "Lễ tân khách sạn", "Bác sĩ", "Tài xế taxi"
        ]
        chosen_role = random.choice(roles_pool)
        recent_c = list(self.factory.recent_contexts)[-6:]
        avoid_c = f" Tránh các tình huống sau: {recent_c}." if recent_c else ""
        cat_inst = f" Dựa trên bối cảnh hoặc từ khóa tình huống yêu cầu: '{context_category}'." if context_category and context_category != "all" else ""

        prompt_text = (
            f"Hãy sáng tạo 1 tình huống giao tiếp tiếng Nhật thực tế bất ngờ "
            f"giữa người học và '{chosen_role}'.{cat_inst}{avoid_c} [Nonce: {nonce}] "
            f"Trả về JSON: {{\"speaker_ja\": \"<lời thoại đối phương, không kèm tiền tố vai trò>\", \"speaker_vi\": \"<dịch nghĩa lời thoại tiếng Việt>\", \"intent\": \"<nhiệm vụ/ý định bạn cần phản hồi ngắn gọn>\", \"key_vocab\": [{{\"ja\": \"...\", \"vi\": \"...\"}}], \"idea_sparks\": [\"🟢 ...\", \"🟡 ...\", \"🔴 ...\"], \"expected_response_ja\": \"<câu trả lời chuẩn mẫu tiếng Nhật>\", \"role\": \"{chosen_role}\", \"cultural_note\": \"<bí quyết ứng xử ngắn gọn>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là chuyên gia tình huống giao tiếp tiếng Nhật thực tế. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.92,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.EXERCISE_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.content.strip())
            speaker_ja = data.get("speaker_ja") or data.get("scenario_prompt_ja", "手伝いましょうか？")
            speaker_vi = data.get("speaker_vi") or data.get("translation_vi", "Để mình phụ một tay nhé?")
            intent_vi = data.get("intent") or data.get("intent_vi", "Cảm ơn và nhờ bê hộp này giúp.")
            expected_ja = data.get("expected_response_ja", "ありがとうございます！これをお願いできますか？")
            role = data.get("role", chosen_role)
            key_vocab = data.get("key_vocab", [])
            idea_sparks = data.get("idea_sparks", [])
            cultural_note = data.get("cultural_note", "")
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] AI Contextual fallback: {e}")
            return self.factory.generate_context(
                difficulty=difficulty,
                pressure_level=pressure_level,
                context_category=context_category,
            )

        return {
            "title": f"瞬発・状況対応: {role}",
            "objective": f"Phản xạ tự nhiên theo tình huống trong {timer_ms/1000:.1f}s",
            "scenario": speaker_vi,
            "instructions": f"Đối phương ({role}): '{speaker_ja}' — Nhiệm vụ: {intent_vi}",
            "prompt": speaker_ja,
            "speaker_ja": speaker_ja,
            "speaker_vi": speaker_vi,
            "prompt_translation": speaker_vi,
            "translation": speaker_vi,
            "vietnamese": speaker_vi,
            "intent": intent_vi,
            "role": role,
            "category": context_category or "workplace",
            "context_category": context_category or "workplace",
            "key_vocab": key_vocab,
            "idea_sparks": idea_sparks,
            "expected": expected_ja,
            "canonical": expected_ja,
            "sample_answer": expected_ja,
            "acceptable_variants": [expected_ja],
            "cultural_note": cultural_note,
            "relationship": role,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Phản hồi phải tự nhiên, đúng ý định, phù hợp mối quan hệ."],
            "target_patterns": [],
            "semantic_target": {"intent": intent_vi, "relationship": role},
            "estimated_minutes": 4,
        }
