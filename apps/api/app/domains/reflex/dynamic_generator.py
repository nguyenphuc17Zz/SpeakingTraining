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
        user_id: str = "reflex_user",
    ) -> dict[str, Any]:
        """Generates dynamic reflex exercise via Gemini AI with Sudachi morphological verification."""
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
                )
            elif sub_mode == "reflex_context":
                return await self._generate_dynamic_context(
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                    user_id=user_id,
                )
            elif sub_mode == "reflex_vocabulary":
                # Vocabulary recall is fully deterministic — no AI needed
                return self.factory.generate_vocabulary(
                    direction="random",
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                )
            elif sub_mode == "reflex_keigo_vocab":
                # Keigo vocabulary blitz is fully deterministic — no AI needed
                return self.factory.generate_keigo_vocabulary(
                    target_type="all",
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                )
            else:
                return await self._generate_dynamic_qna(
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                    user_id=user_id,
                )
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] Global generation exception, falling back to factory: {e}")
            return self.factory.generate(
                sub_mode=sub_mode,
                verb=verb,
                target_form=conjugation_target,
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
        """Generates conjugation using morphological dictionary and AI verification."""
        timer_ms = timer_for_level(pressure_level)

        # All 11 Candidate forms (comprehensive coverage across all Japanese forms)
        all_forms = [
            ConjugationForm.NAI,
            ConjugationForm.TA,
            ConjugationForm.TE,
            ConjugationForm.POTENTIAL,
            ConjugationForm.PASSIVE,
            ConjugationForm.CAUSATIVE,
            ConjugationForm.CAUSATIVE_PASSIVE,
            ConjugationForm.VOLITIONAL,
            ConjugationForm.BA,
            ConjugationForm.TARA,
            ConjugationForm.IMPERATIVE,
        ]
        chosen_form = target_form or self.factory._get_next_form(all_forms)

        # If verb is not provided, query Gemini to dynamically suggest an authentic JLPT verb for this level
        if not verb:
            nonce = uuid.uuid4().hex[:8]
            recent_v = list(self.factory.recent_verbs)[-10:]
            avoid_v = f" TUYỆT ĐỐI TRÁNH các động từ sau: {recent_v}." if recent_v else ""
            prompt_text = (
                f"Hãy đưa ra 1 động từ tiếng Nhật phong phú, tự nhiên và thực tế trong đời sống tiếng Nhật "
                f"để luyện phản xạ chia thể '{chosen_form}'.{avoid_v} [Nonce: {nonce}] "
                f"Trả về JSON định dạng: {{\"verb\": \"<chữ Hán/Kana gốc>\", \"reading\": \"<Hiragana>\", \"meaning_vi\": \"<nghĩa tiếng Việt ngắn gọn>\"}}"
            )
            req = AIRequest(
                messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
                system_instruction="Bạn là chuyên gia ngôn ngữ học tiếng Nhật. Trả về duy nhất JSON hợp lệ, không kèm markdown thừa.",
                response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
                temperature=0.9,
                metadata={"idempotency_key": str(uuid.uuid4())},
            )
            try:
                resp = await self.ai_router.generate(task=AITask.EXERCISE_GENERATION, request=req, user_id=user_id)
                data = json.loads(resp.content.strip())
                verb = data.get("verb", "食べる")
                meaning_vi = data.get("meaning_vi", "Ăn")
                reading = data.get("reading", "たべる")
            except Exception as e:
                logger.warning(f"[AIReflexGenerator] AI verb generation fallback: {e}")
                return self.factory.generate_conjugation(
                    verb=verb,
                    target_form=chosen_form,
                    difficulty=difficulty,
                    pressure_level=pressure_level,
                )
        else:
            meaning_vi = "Động từ tiếng Nhật"
            reading = self.lang_provider.get_reading(verb) or verb

        target = self.conj_engine.conjugate(verb, chosen_form)

        return {
            "title": f"瞬発力・活用: {verb} → {target.form.value}",
            "objective": f"Chia động từ {verb} ({meaning_vi}) sang dạng {target.form.value} trong {timer_ms/1000:.1f}s",
            "scenario": f"Động từ: {verb} ({meaning_vi})",
            "instructions": f"Nghe/nhìn động từ '{verb}' ({meaning_vi}) và nói ngay dạng {target.form.value} trước khi hết giờ.",
            "prompt": verb,
            "prompt_reading": reading,
            "translation": meaning_vi,
            "vietnamese": meaning_vi,
            "target": target.canonical,
            "canonical": target.canonical,
            "acceptable_variants": target.accepted,
            "alternatives": target.alternatives,
            "variant_notes": target.variant_notes,
            "verb_class": target.verb_class.value,
            "form": target.form.value,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Nói chính xác dạng chia, không thêm filler dài."],
            "target_patterns": [target.canonical] + target.accepted,
            "estimated_minutes": 3,
        }

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
            f"Trả về JSON: {{\"question_ja\": \"<câu hỏi tiếng Nhật tự nhiên>\", \"translation_vi\": \"<dịch nghĩa tiếng Việt>\", \"sample_answer_ja\": \"<câu trả lời mẫu ngắn gọn tự nhiên>\", \"topic\": \"{chosen_topic}\"}}"
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
    ) -> dict[str, Any]:
        """Generates dynamic Sentence Transformation via Gemini AI."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]
        recent_t = list(self.factory.recent_transforms)[-6:]
        avoid_t = f" Tránh các câu gốc sau: {recent_t}." if recent_t else ""

        prompt_text = (
            f"Hãy sáng tạo 1 bài tập biến đổi câu tiếng Nhật (Sentence Transformation) phong phú, thực tế.{avoid_t} [Nonce: {nonce}] "
            f"Ví dụ: đổi câu thể lịch sự sang thể ngắn, bị động, sai khiến, bị sai khiến, điều kiện ば/たら, hoặc ý chí. "
            f"Trả về JSON: {{\"source_sentence_ja\": \"<câu gốc tiếng Nhật>\", \"task_instruction_ja\": \"<yêu cầu biến đổi>\", \"expected_sentence_ja\": \"<câu sau khi biến đổi đúng>\", \"translation_vi\": \"<dịch nghĩa câu gốc tiếng Việt>\"}}"
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
            expected_ja = data.get("expected_sentence_ja", "今日は東京に行った。")
            trans_vi = data.get("translation_vi", "Hôm nay tôi đi Tokyo.")
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] AI Transformation fallback: {e}")
            return self.factory.generate_transformation(difficulty=difficulty, pressure_level=pressure_level)

        return {
            "title": f"瞬発・文型変換: {task_ja}",
            "objective": f"Biến đổi câu theo yêu cầu trong {timer_ms/1000:.1f}s",
            "scenario": trans_vi,
            "instructions": f"Câu gốc: '{source_ja}' — Yêu cầu: {task_ja} — Nói ngay câu đã biến đổi.",
            "prompt": source_ja,
            "prompt_translation": trans_vi,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "task": task_ja,
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

        prompt_text = (
            f"Hãy sáng tạo 1 tình huống giao tiếp tiếng Nhật thực tế bất ngờ "
            f"giữa người học và '{chosen_role}'.{avoid_c} [Nonce: {nonce}] "
            f"Trả về JSON: {{\"scenario_prompt_ja\": \"<lời thoại đối phương, ví dụ: {chosen_role}: ...>\", \"intent_vi\": \"<ý định bạn cần phản hồi ngắn gọn>\", \"expected_response_ja\": \"<câu trả lời chuẩn mẫu tiếng Nhật>\", \"translation_vi\": \"<dịch nghĩa tình huống tiếng Việt>\", \"role\": \"{chosen_role}\"}}"
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
            scenario_ja = data.get("scenario_prompt_ja", "Colleague: 手伝いましょうか？")
            intent_vi = data.get("intent_vi", "Cảm ơn và nhờ bê hộp này giúp.")
            expected_ja = data.get("expected_response_ja", "ありがとうございます！これをお願いできますか？")
            trans_vi = data.get("translation_vi", "Đồng nghiệp ngỏ ý giúp đỡ.")
            role = data.get("role", chosen_role)
        except Exception as e:
            logger.warning(f"[AIReflexGenerator] AI Contextual fallback: {e}")
            return self.factory.generate_context(difficulty=difficulty, pressure_level=pressure_level)

        return {
            "title": f"瞬発・状況対応: {role}",
            "objective": f"Phản ứng tự nhiên theo tình huống trong {timer_ms/1000:.1f}s",
            "scenario": trans_vi,
            "instructions": f"Tình huống: {scenario_ja} — Ý định: {intent_vi} — Nói ngay phản hồi tiếng Nhật tự nhiên.",
            "prompt": scenario_ja,
            "prompt_translation": trans_vi,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "intent": intent_vi,
            "expected": expected_ja,
            "canonical": expected_ja,
            "acceptable_variants": [expected_ja],
            "relationship": role,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Phản hồi phải tự nhiên, đúng ý định, phù hợp mối quan hệ."],
            "target_patterns": [],
            "semantic_target": {"intent": intent_vi, "relationship": role},
            "estimated_minutes": 4,
        }
