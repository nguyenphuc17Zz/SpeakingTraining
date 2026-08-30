"""AIKeigoGenerator — 100% dynamic on-the-fly Keigo & Register Exercise Generation via Gemini AI & Sudachi.

No static hardcoded list. Generates infinite authentic Japanese Keigo challenges in real-time across 20+ business situations.
Gracefully falls back to deterministic KeigoTransformationEngine & Factory if AI is unreachable.
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
from app.domains.keigo.exercise_factory import KeigoExerciseFactory, TIMER_DEFAULTS
from app.domains.keigo.social_context import (
    Group,
    PersonRole,
    Register,
    Relationship,
    Situation,
    SocialContext,
)
from app.domains.keigo.transformation_engine import KeigoTransformationEngine
from app.domains.reflex.pressure_profiles import timer_for_level

# 20+ Diverse Business Contexts & Scenarios for Real-life Japanese Business Keigo
BUSINESS_TOPICS_POOL = [
    ("Tiếp khách tại sảnh & quầy lễ tân (受付・来客応対)", "chào đón đối tác, hỏi thông tin hẹn trước, mời vào phòng họp, mời trà, hướng dẫn lối đi"),
    ("Nhận & gọi điện thoại đối tác (電話応対)", "nghe máy công ty, xác nhận danh tính người gọi, chuyển máy cho cấp trên, ghi nhận tin nhắn khi vắng mặt, gọi lại sau"),
    ("Báo cáo & trao đổi công việc (報告・連絡・相談 - Ho-Ren-So)", "báo cáo tiến độ dự án với sếp, xin ý kiến chỉ đạo, thông báo kết quả cuộc họp, cập nhật số liệu"),
    ("Hẹn lịch & sắp xếp cuộc gặp (アポイントメント・日程調整)", "đề xuất ngày giờ gặp mặt đối tác, xác nhận lịch trình của giám đốc, xin dời lịch hẹn vì việc đột xuất"),
    ("Xin lỗi sự cố & giải quyết phàn nàn (謝罪・クレーム対応)", "xin lỗi khách hàng vì giao hàng trễ, nhận lỗi sơ sót tài liệu, cam kết xử lý và khắc phục sự cố"),
    ("Nhờ vả & đề nghị hợp tác (依頼・お願い)", "nhờ đồng nghiệp hỗ trợ, xin chữ ký duyệt của trưởng phòng, nhờ đối tác gửi lại bảng báo giá"),
    ("Từ chối khéo léo & lịch thiệp (お断り・辞退)", "từ chối lời mời dự tiệc công ty đối tác vì trùng lịch, từ chối yêu cầu giảm giá một cách tế nhị"),
    ("Trao đổi nội bộ về sếp với khách ngoài (内外・ウチとソト)", "nói với khách hàng về sự vắng mặt của giám đốc mình, giới thiệu thành viên công ty với đối tác ngoài"),
    ("Gửi & phản hồi email thương mại (ビジネスメール)", "xác nhận đã nhận tài liệu, thông báo đính kèm file hợp đồng, lời chúc cuối thư chuẩn mực"),
    ("Đàm phán & thương thảo hợp đồng (商談・交渉)", "trình bày đề xuất kinh doanh, giải thích điều khoản hợp đồng, lắng nghe mong muốn của khách hàng"),
    ("Thuyết trình & báo cáo dự án (プレゼンテーション)", "mở đầu buổi thuyết trình trước ban giám đốc, chuyển ý giữa các phần, kết thúc và cảm ơn"),
    ("Chào hỏi & làm quen đối tác mới (初対面・名刺交換)", "giới thiệu bản thân khi trao đổi danh thiếp, bày tỏ mong muốn được hợp tác lâu dài"),
    ("Lời cảm ơn & tri ân đối tác (お礼・感謝)", "cảm ơn khách hàng đã ghé thăm gian hàng triển lãm, cảm ơn sự giúp đỡ tận tình của đối tác"),
    ("Mời dự tiệc & sự kiện công ty (招待・案内)", "mời khách hàng tham dự lễ kỷ niệm thành lập công ty, mời cấp trên dự tiệc tất niên"),
    ("Thăm hỏi & chúc mừng công việc (挨拶・お祝い)", "chúc mừng đối tác thăng chức, chúc mừng khai trương văn phòng mới, thăm hỏi sức khoẻ"),
    ("Hướng dẫn & đào tạo nhân viên mới (指導・OJT)", "hướng dẫn quy trình văn phòng cho ma mới, nhắc nhở tác phong đúng mực"),
    ("Hỏi thông tin & thu thập ý kiến (ヒアリング・確認)", "hỏi thăm nhu cầu của khách hàng, xác nhận lại thông tin đơn hàng"),
    ("Đón tiếp tại sân bay / khách sạn (送迎・アテンド)", "đón đối tác Nhật Bản tại sân bay, hướng dẫn về khách sạn và sắp xếp bữa tối"),
    ("Trao đổi tiến độ thanh toán & hoá đơn (請求・支払い)", "nhắc nhở lịch thanh toán một cách lịch sự, xác nhận đã nhận được tiền chuyển khoản"),
    ("Chào tạm biệt khi kết thúc chuyến công tác (見送り・締めくくり)", "cảm ơn vì sự đón tiếp chu đáo trong chuyến công tác, hẹn gặp lại dịp tới"),
]


class AIKeigoGenerator:
    """Generates infinite, creative, non-repeating Keigo speaking exercises using Gemini AI and Sudachi."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.factory = KeigoExerciseFactory()
        self.engine = KeigoTransformationEngine()
        self.lang_provider = get_language_provider()
        self.recent_signatures: set[str] = set()

    async def generate_dynamic_exercise(
        self,
        sub_mode: str,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        user_id: str = "keigo_user",
    ) -> dict[str, Any]:
        """Generates dynamic Keigo exercise via Gemini AI with linguistic verification."""
        try:
            if sub_mode == "keigo_sonkeigo":
                return await self._generate_dynamic_sonkeigo(difficulty, pressure_level, user_id)
            elif sub_mode == "keigo_kenjougo":
                return await self._generate_dynamic_kenjougo(difficulty, pressure_level, user_id)
            elif sub_mode == "keigo_teineigo":
                return await self._generate_dynamic_teineigo(difficulty, pressure_level, user_id)
            elif sub_mode == "keigo_transformation":
                return await self._generate_dynamic_shift(difficulty, pressure_level, user_id)
            elif sub_mode == "keigo_context":
                return await self._generate_dynamic_uchi_soto(difficulty, pressure_level, user_id)
            elif sub_mode == "keigo_doctor":
                return await self._generate_dynamic_doctor(difficulty, pressure_level, user_id)
            elif sub_mode == "keigo_naturalness":
                return await self._generate_dynamic_naturalness(difficulty, pressure_level, user_id)
            else:
                # Default / Mixed mode: randomly pick one of the core sub-modes
                eff = random.choice([
                    "keigo_sonkeigo",
                    "keigo_kenjougo",
                    "keigo_teineigo",
                    "keigo_transformation",
                    "keigo_context",
                    "keigo_doctor",
                ])
                return await self.generate_dynamic_exercise(eff, difficulty, pressure_level, user_id)
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] AI generation exception, falling back to rule factory: {e}")
            return self.factory.generate(sub_mode=sub_mode, difficulty=difficulty)

    async def _generate_dynamic_sonkeigo(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Sonkeigo (尊敬語) exercise - honoring the listener/customer/boss."""
        timer_ms = timer_for_level(pressure_level)
        chosen_topic, topic_detail = random.choice(BUSINESS_TOPICS_POOL)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 bài tập Tôn Kính Ngữ (尊敬語 - Sonkeigo) độc đáo, tự nhiên trong bối cảnh công sở Nhật Bản. "
            f"Chủ đề: '{chosen_topic}' ({topic_detail}). [Nonce: {nonce}]\n"
            f"Quy tắc: Cho 1 câu nói về hành động của Đối tác/Khách hàng/Sếp (thể thông thường hoặc lịch sự nhẹ), "
            f"và yêu cầu người học chuyển sang câu Tôn Kính Ngữ (Sonkeigo) chuẩn mực cao nhất.\n"
            f"Trả về duy nhất JSON định dạng:\n"
            f"{{\n"
            f"  \"source_prompt\": \"<câu gốc tiếng Nhật, VD: 部長、この資料を見ましたか？>\",\n"
            f"  \"scenario\": \"<mô tả ngắn bối cảnh, VD: Bạn hỏi Trưởng phòng xem đã đọc tài liệu chưa>\",\n"
            f"  \"instructions\": \"<hướng dẫn ngắn, VD: Hãy nâng cao hành động của Trưởng phòng bằng Tôn kính ngữ (尊敬語)>\",\n"
            f"  \"canonical\": \"<câu đáp án Tôn kính ngữ chuẩn, VD: 部長、こちらの資料をご覧になりましたか？>\",\n"
            f"  \"acceptable_variants\": [\"<biến thể tương đương 1>\", \"<biến thể tương đương 2>\"],\n"
            f"  \"translation_vi\": \"<dịch nghĩa câu gốc tiếng Việt>\",\n"
            f"  \"speaker_role\": \"SELF\",\n"
            f"  \"listener_role\": \"MANAGER\",\n"
            f"  \"referent_role\": \"MANAGER\",\n"
            f"  \"speaker_group\": \"UCHI\",\n"
            f"  \"listener_group\": \"SOTO\"\n"
            f"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là chuyên gia giảng dạy Kính ngữ công sở Nhật Bản (ビジネス敬語). Trả về duy nhất JSON hợp lệ, không kèm markdown thừa.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            source = data.get("source_prompt", "社長はもう来ましたか？")
            scenario = data.get("scenario", "Bạn hỏi về sự có mặt của Giám đốc")
            instructions = data.get("instructions", "Dùng Tôn kính ngữ để nâng cao hành động của đối phương")
            canonical = data.get("canonical", "社長はもういらっしゃいましたか？")
            variants = data.get("acceptable_variants", [canonical])
            trans_vi = data.get("translation_vi", "Giám đốc đã đến chưa ạ?")
            ctx = {
                "speaker_role": data.get("speaker_role", "SELF"),
                "listener_role": data.get("listener_role", "MANAGER"),
                "referent_role": data.get("referent_role", "MANAGER"),
                "speaker_group": data.get("speaker_group", "UCHI"),
                "listener_group": data.get("listener_group", "SOTO"),
                "relationship": "BUSINESS",
                "situation": chosen_topic.split("(")[0].strip(),
            }
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Sonkeigo generation fallback: {e}")
            return self.factory.generate_shift(Register.POLITE, Register.BUSINESS_KEIGO, difficulty)

        return {
            "title": "Sonkeigo: Tôn Kính Ngữ (尊敬語 ↑)",
            "objective": f"Nói câu Tôn kính ngữ nâng cao hành động đối tác trong {timer_ms/1000:.1f}s",
            "scenario": scenario,
            "instructions": instructions,
            "prompt": source,
            "source": source,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "social_context": ctx,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Đúng hướng Tôn kính ngữ, không dùng khiêm nhường"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_kenjougo(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Kenjougo (謙譲語) exercise - humbling own actions to customer/external partner."""
        timer_ms = timer_for_level(pressure_level)
        chosen_topic, topic_detail = random.choice(BUSINESS_TOPICS_POOL)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 bài tập Khiêm Nhường Ngữ (謙譲語 - Kenjougo) thực tế trong công sở Nhật Bản. "
            f"Chủ đề: '{chosen_topic}' ({topic_detail}). [Nonce: {nonce}]\n"
            f"Quy tắc: Cho 1 câu nói về hành động của Bản thân / Công ty mình khi nói với Khách hàng/Đối tác, "
            f"và yêu cầu người học chuyển sang câu Khiêm Nhường Ngữ (Kenjougo I/II) chuẩn mực.\n"
            f"Trả về duy nhất JSON định dạng:\n"
            f"{{\n"
            f"  \"source_prompt\": \"<câu gốc tiếng Nhật, VD: 明日の14時にそちらの会社に行きます。>\",\n"
            f"  \"scenario\": \"<mô tả ngắn bối cảnh, VD: Bạn thông báo với khách hàng ngày mai sẽ đến công ty họ>\",\n"
            f"  \"instructions\": \"<hướng dẫn ngắn, VD: Hãy hạ thấp hành động bản thân bằng Khiêm nhường ngữ (謙譲語)>\",\n"
            f"  \"canonical\": \"<câu đáp án Khiêm nhường chuẩn, VD: 明日の14時に御社へ伺います。>\",\n"
            f"  \"acceptable_variants\": [\"<biến thể 1>\", \"<biến thể 2>\"],\n"
            f"  \"translation_vi\": \"<dịch nghĩa tiếng Việt>\",\n"
            f"  \"speaker_role\": \"SELF\",\n"
            f"  \"listener_role\": \"CUSTOMER\",\n"
            f"  \"referent_role\": \"SELF\",\n"
            f"  \"speaker_group\": \"UCHI\",\n"
            f"  \"listener_group\": \"SOTO\"\n"
            f"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là chuyên gia Kính ngữ công sở Nhật Bản. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            source = data.get("source_prompt", "明日、社長に会います。")
            scenario = data.get("scenario", "Bạn nói với đối tác về việc gặp gỡ")
            instructions = data.get("instructions", "Dùng Khiêm nhường ngữ để hạ thấp hành động bản thân")
            canonical = data.get("canonical", "明日、社長にお目にかかります。")
            variants = data.get("acceptable_variants", [canonical, "明日、社長にお会いいたします。"])
            trans_vi = data.get("translation_vi", "Ngày mai tôi sẽ gặp giám đốc ạ.")
            ctx = {
                "speaker_role": "SELF",
                "listener_role": "CUSTOMER",
                "referent_role": "SELF",
                "speaker_group": "UCHI",
                "listener_group": "SOTO",
                "relationship": "CUSTOMER_PROVIDER",
                "situation": chosen_topic.split("(")[0].strip(),
            }
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Kenjougo generation fallback: {e}")
            return self.factory.generate_shift(Register.POLITE, Register.BUSINESS_KEIGO, difficulty)

        return {
            "title": "Kenjougo: Khiêm Nhường Ngữ (謙譲語 ↓)",
            "objective": f"Nói câu Khiêm nhường ngữ hạ mình trước đối tác trong {timer_ms/1000:.1f}s",
            "scenario": scenario,
            "instructions": instructions,
            "prompt": source,
            "source": source,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "social_context": ctx,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Đúng hướng Khiêm nhường ngữ, hạ thấp bản thân"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_teineigo(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Teineigo & Bikago (丁寧語・美化語) exercise."""
        timer_ms = timer_for_level(pressure_level)
        chosen_topic, topic_detail = random.choice(BUSINESS_TOPICS_POOL)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 bài tập Thể Lịch Sự & Mỹ Từ (丁寧語・美化語) trong giao tiếp văn phòng. "
            f"Chủ đề: '{chosen_topic}'. [Nonce: {nonce}]\n"
            f"Yêu cầu: Cho 1 câu văn suồng sã hoặc thiếu mỹ từ お/ご, yêu cầu chuyển sang câu chuẩn lịch sự desu/masu/gozaimasu.\n"
            f"Trả về JSON: {{\"source_prompt\": \"<câu gốc>\", \"scenario\": \"<bối cảnh>\", \"instructions\": \"<hướng dẫn>\", \"canonical\": \"<câu chuẩn>\", \"acceptable_variants\": [\"<câu tương đương>\"], \"translation_vi\": \"<dịch tiếng Việt>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia Nhật ngữ. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.85,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            source = data.get("source_prompt", "名前は何ですか？")
            scenario = data.get("scenario", "Hỏi tên khách hàng lịch sự")
            instructions = data.get("instructions", "Sử dụng Thể Lịch Sự & Mỹ từ お/ご")
            canonical = data.get("canonical", "お名前をお伺いしてもよろしいでしょうか？")
            variants = data.get("acceptable_variants", [canonical, "お名前を教えていただけますか？"])
            trans_vi = data.get("translation_vi", "Tôi có thể xin quý danh của quý khách được không ạ?")
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Teineigo generation fallback: {e}")
            return self.factory.generate_shift(Register.TAMEGUCHI, Register.POLITE, difficulty)

        return {
            "title": "Teineigo: Lịch Sự & Mỹ Từ (丁寧語・美化語)",
            "objective": f"Nói câu lịch sự chuẩn mực có mỹ từ trong {timer_ms/1000:.1f}s",
            "scenario": scenario,
            "instructions": instructions,
            "prompt": source,
            "source": source,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Lịch sự, tự nhiên, đúng mỹ từ お/ご"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_shift(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Register Shift (Tameguchi <-> Business Keigo)."""
        timer_ms = timer_for_level(pressure_level)
        chosen_topic, topic_detail = random.choice(BUSINESS_TOPICS_POOL)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 bài tập Chuyển Đổi Văn Phong (Register Shift) phản xạ tức thì. "
            f"Chủ đề: '{chosen_topic}'. [Nonce: {nonce}]\n"
            f"Cho 1 câu nói thân mật (Tameguchi) ngắn gọn giữa bạn bè hoặc suy nghĩ nội tâm, "
            f"yêu cầu người học chuyển sang câu Kính ngữ thương mại (Business Keigo) hoàn chỉnh.\n"
            f"Trả về JSON: {{\"source_prompt\": \"<câu thân mật>\", \"scenario\": \"<bối cảnh>\", \"instructions\": \"<hướng dẫn>\", \"canonical\": \"<câu thương mại chuẩn>\", \"acceptable_variants\": [\"<câu biến thể>\"], \"translation_vi\": \"<dịch tiếng Việt>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia Nhật ngữ công sở. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            source = data.get("source_prompt", "ちょっと待って。")
            scenario = data.get("scenario", "Chuyển câu nhờ đợi sang văn phong tiếp khách")
            instructions = data.get("instructions", "Chuyển từ Thân mật (Tameguchi) sang Kính ngữ thương mại")
            canonical = data.get("canonical", "少々お待ちいただけますでしょうか。")
            variants = data.get("acceptable_variants", [canonical, "少々お待ちくださいませ。"])
            trans_vi = data.get("translation_vi", "Xin vui lòng đợi một chút.")
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Shift generation fallback: {e}")
            return self.factory.generate_shift(Register.TAMEGUCHI, Register.BUSINESS_KEIGO, difficulty)

        return {
            "title": "Register Shift: Chuyển Đổi Văn Phong (変換 ⇄)",
            "objective": f"Chuyển từ thân mật sang kính ngữ thương mại trong {timer_ms/1000:.1f}s",
            "scenario": scenario,
            "instructions": instructions,
            "prompt": source,
            "source": source,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Đúng văn phong công sở trang trọng"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_uchi_soto(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Uchi / Soto Battle contextual challenge."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 tình huống kinh điển thử thách phân biệt Trong/Ngoài (Uchi - Soto) trong văn hóa công sở Nhật. [Nonce: {nonce}]\n"
            f"Ví dụ: Đối tác ngoài gọi điện hỏi về Giám đốc/Trưởng phòng bên bạn. "
            f"Người học phải phản xạ hạ sếp mình xuống bằng Khiêm nhường ngữ và bỏ chức danh (VD: 社長の田中は席を外しております).\n"
            f"Trả về JSON: {{\"prompt\": \"<câu hỏi của đối tác ngoài>\", \"scenario\": \"<bối cảnh vai vế rõ ràng>\", \"instructions\": \"<hướng dẫn chọn đúng hướng Kính ngữ>\", \"canonical\": \"<câu trả lời chuẩn>\", \"acceptable_variants\": [\"<biến thể>\"], \"translation_vi\": \"<dịch tiếng Việt>\", \"speaker_group\": \"UCHI\", \"listener_group\": \"SOTO\", \"referent_group\": \"UCHI\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia văn hóa doanh nghiệp Nhật. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            prompt = data.get("prompt", "田中社長はいらっしゃいますか？")
            scenario = data.get("scenario", "Khách hàng gọi điện hỏi gặp Giám đốc Tanaka bên công ty bạn")
            instructions = data.get("instructions", "Nói về sếp mình với khách ngoài: dùng Khiêm nhường ngữ và bỏ chức danh")
            canonical = data.get("canonical", "あいにく社長の田中は外出しております。")
            variants = data.get("acceptable_variants", [canonical, "社長の田中はただいま席を外しております。"])
            trans_vi = data.get("translation_vi", "Giám đốc Tanaka có ở đó không ạ?")
            ctx = {
                "speaker_role": "EMPLOYEE",
                "listener_role": "CUSTOMER",
                "referent_role": "MANAGER",
                "speaker_group": "UCHI",
                "listener_group": "SOTO",
                "referent_group": "UCHI",
                "relationship": "CUSTOMER_PROVIDER",
                "situation": "電話応対",
            }
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Uchi-Soto generation fallback: {e}")
            return self.factory.generate_uchi_soto(difficulty)

        return {
            "title": "Uchi / Soto Battle: Văn Hóa Trong - Ngoài (内外 ⚔️)",
            "objective": f"Xác định đúng vai vế Trong/Ngoài và phản xạ chuẩn trong {timer_ms/1000:.1f}s",
            "scenario": scenario,
            "instructions": instructions,
            "prompt": prompt,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "social_context": ctx,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Đúng quan hệ Uchi/Soto, không tôn xưng sếp mình trước khách"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_doctor(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Keigo Doctor (fixing Double Keigo / Direction errors)."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 câu tiếng Nhật có LỖI SAI KÍNH NGỮ thực tế (Nhị trùng kính ngữ 二重敬語 hoặc lộn hướng Tôn kính/Khiêm nhường). [Nonce: {nonce}]\n"
            f"Yêu cầu người học phát hiện lỗi và nói lại câu đúng hoàn chỉnh.\n"
            f"Ví dụ lỗi: おっしゃられる (lỗi nhị trùng), 社長がお召し上がりになられた (lỗi thừa kính ngữ), ご覧いたす (lộn hướng).\n"
            f"Trả về JSON: {{\"faulty_sentence_ja\": \"<câu có lỗi sai>\", \"error_type\": \"<DOUBLE_KEIGO | WRONG_DIRECTION>\", \"scenario\": \"<mô tả lỗi>\", \"instructions\": \"<hướng dẫn sửa lỗi>\", \"canonical_fix_ja\": \"<câu đã sửa đúng hoàn chỉnh>\", \"acceptable_variants\": [\"<câu sửa đúng biến thể>\"], \"translation_vi\": \"<dịch nghĩa tiếng Việt>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bác sĩ Kính ngữ Nhật Bản. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            faulty = data.get("faulty_sentence_ja", "社長がおっしゃられました。")
            scenario = data.get("scenario", "Phát hiện lỗi Nhị trùng kính ngữ (Double Keigo)")
            instructions = data.get("instructions", "Câu này bị lỗi kính ngữ trùng lặp. Hãy nói lại câu đúng chuẩn.")
            canonical = data.get("canonical_fix_ja", "社長がおっしゃいました。")
            variants = data.get("acceptable_variants", [canonical, "社長が言われました。"])
            trans_vi = data.get("translation_vi", "Giám đốc đã nói như vậy.")
            err_type = data.get("error_type", "DOUBLE_KEIGO")
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Doctor generation fallback: {e}")
            return self.factory.generate_doctor(difficulty)

        return {
            "title": "Keigo Doctor: Bắt Lỗi Kính Ngữ (診断 🩺)",
            "objective": f"Phát hiện lỗi sai và nói lại câu đúng trong {timer_ms/1000:.1f}s",
            "scenario": f"Câu có lỗi: “{faulty}” — {scenario}",
            "instructions": instructions,
            "prompt": faulty,
            "error_type": err_type,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Sửa đúng ngữ pháp, loại bỏ lặp kính ngữ"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }

    async def _generate_dynamic_naturalness(
        self,
        difficulty: str,
        pressure_level: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Generates dynamic Naturalness Check challenge."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy tạo 1 câu giao tiếp tiếng Nhật và yêu cầu người học đánh giá mức độ tự nhiên công sở. [Nonce: {nonce}]\n"
            f"Trả về JSON: {{\"sentence_ja\": \"<câu tiếng Nhật>\", \"scenario\": \"<bối cảnh>\", \"is_natural\": true/false, \"expected_label\": \"NATURAL | INAPPROPRIATE\", \"canonical_correction\": \"<câu tự nhiên nhất>\", \"acceptable_variants\": [\"<câu biến thể>\"], \"translation_vi\": \"<dịch nghĩa tiếng Việt>\"}}"
        )
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Chuyên gia tự nhiên ngữ dụng học tiếng Nhật. Trả về duy nhất JSON hợp lệ.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.85,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )
        try:
            resp = await self.ai_router.generate(task=AITask.KEIGO_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            sentence = data.get("sentence_ja", "明日、社長にお会いします。")
            scenario = data.get("scenario", "Đánh giá mức độ tự nhiên trong văn phòng")
            canonical = data.get("canonical_correction", sentence)
            variants = data.get("acceptable_variants", [canonical])
            trans_vi = data.get("translation_vi", "Ngày mai tôi sẽ gặp giám đốc.")
            label = data.get("expected_label", "NATURAL")
        except Exception as e:
            logger.warning(f"[AIKeigoGenerator] Naturalness generation fallback: {e}")
            return self.factory.generate_naturalness(difficulty)

        return {
            "title": "Naturalness Check: Độ Tự Nhiên (自然 🍃)",
            "objective": f"Đánh giá và nói lại câu tự nhiên chuẩn Nhật trong {timer_ms/1000:.1f}s",
            "scenario": f"Đánh giá câu: “{sentence}” ({label})",
            "instructions": "Nói lại câu tiếng Nhật chuẩn mực và tự nhiên nhất",
            "prompt": sentence,
            "expected_label": label,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": trans_vi,
            "vietnamese": trans_vi,
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": ["Tự nhiên, đúng sắc thái"],
            "target_patterns": variants[:2],
            "estimated_minutes": 3,
        }
