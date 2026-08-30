"""AISituationsGenerator — 100% dynamic on-the-fly Situational Roleplay Generation via Gemini AI.

Generates infinite, creative, immersive Japanese conversational roleplays across:
1. Predefined core categories (Izakaya, Retail, Transportation, Healthcare, Workplace, Travel)
2. Infinite AI Random Sandbox (`category="infinite"`) covering 100,000+ real-life Japanese scenarios
3. User-defined Custom Topics / Freeform Prompts (`custom_topic="Thuê nhà qua bất động sản"`, etc.)
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
from app.domains.reflex.pressure_profiles import timer_for_level
from app.domains.situations.scenario_generator import ScenarioGenerator

SITUATIONAL_CATEGORIES = {
    "food": {
        "ja": "飲食・居酒屋 (Ẩm thực & Quán nhậu)",
        "locations": ["Quán nhậu Izakaya truyền thống", "Quán Ramen tại Shinjuku", "Quán Cafe bánh ngọt Shibuya", "Nhà hàng Sushi băng chuyền"],
        "roles": ["Phục vụ quán (店員)", "Chủ quán (店長)", "Đầu bếp (板前)"],
        "examples": ["Đặt bàn 2 người, gọi bia tươi Nama-biiru và xiên nướng Yakitori, yêu cầu tách hóa đơn Betsu-betsu"],
    },
    "retail": {
        "ja": "買い物・コンビニ (Mua sắm & Konbini)",
        "locations": ["Cửa hàng tiện lợi 7-Eleven", "Hiệu thuốc Matsumoto Kiyoshi", "Siêu thị bách hóa Aeon", "Cửa hàng đồ điện tử Yodobashi Camera"],
        "roles": ["Thu ngân (レジ係)", "Nhân viên bán hàng (店員)", "Dược sĩ (薬剤師)"],
        "examples": ["Hâm nóng cơm bento, từ chối lấy túi nilon (Fukuro wa kekkou desu), thanh toán qua thẻ IC"],
    },
    "transportation": {
        "ja": "交通・駅・空港 (Giao thông & Nhà ga)",
        "locations": ["Quầy vé ga Tokyo Station", "Cửa soát vé Shinkansen", "Quầy thông tin Sân bay Haneda", "Trên xe Taxi tại Kyoto"],
        "roles": ["Nhân viên nhà ga (駅員)", "Tài xế Taxi (運転手)", "Nhân viên quầy vé (窓口係)"],
        "examples": ["Mua vé Shinkansen đi Osaka ghế chỉ định Shiteiseki, hỏi cửa chuyển tàu Norikae, nạp tiền thẻ Suica"],
    },
    "healthcare": {
        "ja": "医療・薬局・緊急 (Y tế & Hiệu thuốc & Khẩn cấp)",
        "locations": ["Phòng khám Nội khoa (内科クリニック)", "Hiệu thuốc kê đơn (調剤薬局)", "Đồn cảnh sát Kouban (交番)", "Bệnh viện đa khoa"],
        "roles": ["Bác sĩ khám bệnh (医師)", "Y tá tiếp tân (受付)", "Cảnh sát trực ban (警察官)"],
        "examples": ["Mô tả triệu chứng đau họng và sốt từ đêm qua, hỏi cách uống thuốc ngày 3 lần sau ăn, báo rơi ví tiền tại ga"],
    },
    "workplace": {
        "ja": "ビジネス・職場 (Công sở & Họp hành)",
        "locations": ["Phòng họp công ty đối tác tại Marunouchi", "Bàn làm việc văn phòng", "Hành lang công ty", "Tiệc rượu giao lưu Nomikai"],
        "roles": ["Trưởng phòng đối tác (部長)", "Đồng nghiệp cùng team (同僚)", "Khách hàng doanh nghiệp (取引先)"],
        "examples": ["Chào hỏi trao đổi danh thiếp Meishi Koukan, báo cáo tiến độ dự án Hou-Ren-So, xin phép nghỉ ốm đột xuất"],
    },
    "travel": {
        "ja": "ホテル・観光・旅行 (Khách sạn & Du lịch)",
        "locations": ["Quầy lễ tân Khách sạn Ryokan Onsen", "Khách sạn thương gia APA Hotel", "Trung tâm thông tin du lịch Asakusa", "Điểm thuê Kimono"],
        "roles": ["Lễ tân khách sạn (フロント)", "Hướng dẫn viên du lịch (案内係)", "Chủ nhà trọ Ryokan (女将)"],
        "examples": ["Check-in nhận phòng đã đặt online, gửi hành lý trước giờ nhận phòng, hỏi quán ăn ngon đặc sản địa phương"],
    },
}

INFINITE_RANDOM_SEEDS = [
    {"loc": "Công ty Bất động sản tại Shinjuku", "role": "Nhân viên môi giới (不動産屋)", "topic": "Tìm thuê căn hộ 1DK gần ga tàu, hỏi tiền cọc Shikikin và Reikin"},
    {"loc": "Phòng phỏng vấn việc làm thêm (Baito)", "role": "Quản lý cửa hàng (店長)", "topic": "Phỏng vấn xin việc làm thêm tại tiệm bánh ngọt, hỏi lịch ca làm việc Shifuto"},
    {"loc": "Ủy ban Quận Shiyakusho", "role": "Cán bộ hành chính (窓口担当)", "topic": "Đăng ký địa chỉ cư trú Juuminhyou và làm thủ tục bảo hiểm quốc dân Kokumin Kenkou Hoken"},
    {"loc": "Tiệm làm tóc Hair Salon tại Omotesando", "role": "Thợ cắt tóc (美容師)", "topic": "Yêu cầu cắt ngắn 2 bên, tỉa bớt ngọn và nhuộm màu nâu tự nhiên"},
    {"loc": "Chợ đồ cũ Mercari / Gặp nhận đồ", "role": "Người bán hàng trên app (出品者)", "topic": "Xác nhận tình trạng hàng hóa, hỏi bớt giá và hẹn địa điểm giao nhận"},
    {"loc": "Khu chung cư Manshon", "role": "Bác hàng xóm người Nhật (隣人)", "topic": "Hỏi cách phân loại rác cồng kềnh Sodai Gomi và chào hỏi quà mừng chuyển đến"},
    {"loc": "Trạm thuê xe tự lái Rental Car Hokkaido", "role": "Nhân viên trạm thuê xe (受付)", "topic": "Thuê xe 4 chỗ có thẻ ETC và lốp đi tuyết, hỏi quy định đổ đầy xăng khi trả"},
    {"loc": "Phòng khám Thú y Animal Clinic", "role": "Bác sĩ thú y (獣医師)", "topic": "Dẫn mèo đi khám vì bỏ ăn từ hôm qua, hỏi lịch tiêm phòng định kỳ"},
    {"loc": "Phòng tập Gym 24/7", "role": "Huấn luyện viên (トレーナー)", "topic": "Đăng ký thẻ hội viên tháng, hỏi cách sử dụng tủ khóa và thuê PT riêng"},
    {"loc": "Cửa hàng Anime Figure tại Akihabara", "role": "Nhân viên bán hàng Otaku (店員)", "topic": "Tìm mua mô hình nhân vật phiên bản giới hạn, hỏi chính sách miễn thuế Tax-Free"},
    {"loc": "Quán Trà Đạo truyền thống tại Kyoto", "role": "Nghệ nhân trà đạo (茶道師範)", "topic": "Trải nghiệm nghi thức thưởng trà Matcha và bánh Wagashi truyền thống"},
    {"loc": "Đồn Cảnh Sát Kouban ga Shibuya", "role": "Cảnh sát trực ban (警察官)", "topic": "Báo bị khóa bánh xe đạp do đỗ sai quy định và hỏi thủ tục nộp phạt lấy xe"},
]


class AISituationsGenerator:
    """Generates infinite, creative, realistic Situational Roleplay challenges using Gemini AI."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)
        self.factory = ScenarioGenerator()

    async def generate_dynamic_exercise(
        self,
        category: str | None = None,
        custom_topic: str | None = None,
        difficulty: str = "normal",
        pressure_level: str = "normal",
        duration: int = 5,
        mode: str = "standard",
        user_id: str = "situations_user",
    ) -> dict[str, Any]:
        """Generates dynamic situational roleplay exercise via Gemini AI supporting custom topics and infinite mode."""
        timer_ms = timer_for_level(pressure_level)
        nonce = uuid.uuid4().hex[:8]

        # 1. Determine Context & NPC Setting
        is_custom = bool(custom_topic and custom_topic.strip())
        is_infinite = category == "infinite" or category == "random"

        if is_custom:
            chosen_cat_key = "custom"
            cat_label = f"Tự do • {custom_topic.strip()[:30]}"
            chosen_loc = f"Bối cảnh tự do: {custom_topic.strip()}"
            chosen_npc_role = "Nhân vật đối thoại phù hợp bối cảnh"
            scenario_instruction = f"Bối cảnh người dùng tự yêu cầu: '{custom_topic.strip()}'. Hãy xây dựng một tình huống hội thoại tiếng Nhật cực kỳ chân thực, đúng phong tục văn hóa đời sống Nhật Bản theo chủ đề này."
        elif is_infinite:
            seed_choice = random.choice(INFINITE_RANDOM_SEEDS)
            chosen_cat_key = "infinite"
            cat_label = "無限 • Vô Tận Ngẫu Nhiên"
            chosen_loc = seed_choice["loc"]
            chosen_npc_role = seed_choice["role"]
            scenario_instruction = f"Bối cảnh độc đáo: {chosen_loc}. Chủ đề: {seed_choice['topic']}. Nhân vật NPC: {chosen_npc_role}."
        else:
            if not category or category not in SITUATIONAL_CATEGORIES:
                chosen_cat_key = random.choice(list(SITUATIONAL_CATEGORIES.keys()))
            else:
                chosen_cat_key = category

            cat_info = SITUATIONAL_CATEGORIES[chosen_cat_key]
            chosen_loc = random.choice(cat_info["locations"])
            chosen_npc_role = random.choice(cat_info["roles"])
            cat_label = cat_info["ja"]
            scenario_instruction = f"Bối cảnh: {chosen_loc} (Chuyên đề: {cat_label}). Nhân vật NPC: {chosen_npc_role}."

        prompt_text = (
            f"Hãy tạo 1 tình huống giao tiếp thực chiến tiếng Nhật (Situational Roleplay) chân thực, sống động và giàu tính thực tế đời sống Nhật Bản. [Nonce: {nonce}]\n"
            f"{scenario_instruction}\n\n"
            f"Yêu cầu:\n"
            f"1. Xác định địa điểm cụ thể và nhân vật NPC đối thoại bằng tiếng Nhật.\n"
            f"2. NPC mở đầu bằng 1 câu thoại tiếng Nhật tự nhiên, ngữ điệu chân thực và đúng vai trò.\n"
            f"3. Người học có 2-3 mục tiêu nhiệm vụ rõ ràng (Goals) cần phản xạ đối đáp tiếng Nhật để hoàn thành.\n"
            f"4. Đưa ra 1 sự kiện phát sinh bất ngờ (Twist / Unexpected Incident) phù hợp với bối cảnh này để thử thách phản xạ.\n"
            f"5. Cung cấp câu đáp án mẫu tiếng Nhật hoàn hảo, các mẫu câu gợi ý hữu ích và từ vựng.\n\n"
            f"Trả về JSON định dạng duy nhất:\n"
            f"{{\n"
            f"  \"situation_title\": \"<tên ngắn gọn tình huống, VD: Đặt phòng tại Ryokan Onsen>\",\n"
            f"  \"location_name\": \"<tên địa điểm, VD: {chosen_loc}>\",\n"
            f"  \"npc_name\": \"<tên và vai trò NPC tiếng Nhật & Việt, VD: 山田 (Lễ tân Ryokan)>\",\n"
            f"  \"npc_personality\": \"<thái độ/tính cách, VD: Nhã nhặn, kính ngữ chuẩn mực>\",\n"
            f"  \"npc_opening_dialogue\": \"<câu thoại mở đầu bằng tiếng Nhật>\",\n"
            f"  \"npc_dialogue_vi\": \"<dịch tiếng Việt câu thoại NPC>\",\n"
            f"  \"user_role\": \"<vai trò người học, VD: Khách du lịch>\",\n"
            f"  \"goals\": [\n"
            f"    {{\"id\": \"g1\", \"task\": \"<nhiệm vụ 1>\", \"intent\": \"<intent_key>\"}},\n"
            f"    {{\"id\": \"g2\", \"task\": \"<nhiệm vụ 2>\", \"intent\": \"<intent_key>\"}}\n"
            f"  ],\n"
            f"  \"unexpected_event\": \"<sự kiện bất ngờ phát sinh>\",\n"
            f"  \"canonical_response\": \"<câu đáp án mẫu tiếng Nhật hoàn hảo>\",\n"
            f"  \"acceptable_variants\": [\"<biến thể 1>\", \"<biến thể 2>\"],\n"
            f"  \"useful_phrases\": [\"<mẫu câu 1>\", \"<mẫu câu 2>\"],\n"
            f"  \"vocabulary_hints\": \"<gợi ý từ vựng>\"\n"
            f"}}"
        )

        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là đạo diễn kịch bản hội thoại tiếng Nhật thực chiến hàng đầu. Trả về duy nhất JSON hợp lệ, không markdown thừa.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.95 if is_infinite or is_custom else 0.9,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )

        try:
            resp = await self.ai_router.generate(task=AITask.SITUATIONAL_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            title = data.get("situation_title", f"Tình huống tại {chosen_loc}")
            loc_name = data.get("location_name", chosen_loc)
            npc_name = data.get("npc_name", f"Nhân viên ({chosen_npc_role})")
            npc_personality = data.get("npc_personality", "Lịch sự, nhã nhặn")
            opening = data.get("npc_opening_dialogue", "いらっしゃいませ！")
            opening_vi = data.get("npc_dialogue_vi", "Kính chào quý khách!")
            user_role = data.get("user_role", "Khách hàng")
            goals = data.get("goals", [{"id": "g1", "task": "Hoàn thành đối thoại", "intent": "GENERAL"}])
            event = data.get("unexpected_event", "Tình huống diễn ra bình thường")
            canonical = data.get("canonical_response", opening)
            variants = data.get("acceptable_variants", [canonical])
            phrases = data.get("useful_phrases", [])
            vocab = data.get("vocabulary_hints", "")
        except Exception as e:
            logger.warning(f"[AISituationsGenerator] Dynamic generation fallback: {e}")
            scenario = self.factory.generate(category=chosen_cat_key if chosen_cat_key in SITUATIONAL_CATEGORIES else "food", difficulty=difficulty, duration_minutes=duration, mode=mode)
            first_npc = scenario["actors"][0] if scenario.get("actors") else {}
            title = f"Tình huống tại {scenario['location']['subtype']}"
            loc_name = scenario["location"]["subtype"]
            npc_name = f"{first_npc.get('identity', {}).get('name', 'Nhân viên')} ({first_npc.get('identity', {}).get('role', 'clerk')})"
            npc_personality = "Thân thiện"
            opening = "いらっしゃいませ。ご注文はお決まりでしょうか？"
            opening_vi = "Kính chào quý khách. Quý khách đã chọn được món chưa ạ?"
            user_role = scenario.get("user_role", {}).get("role", "Khách hàng")
            goals = [{"id": f"g_{i}", "task": g.get("description", "Nhiệm vụ"), "intent": g.get("required_intent", "REQUEST")} for i, g in enumerate(scenario.get("goals", []))]
            event = "Quán đông khách, hãy gọi món dứt khoát"
            canonical = "すみません、これをひとつお願いします。"
            variants = [canonical]
            phrases = ["これをお願いします", "いくらですか"]
            vocab = "すみません (Xin lỗi/Làm phiền)"

        return {
            "title": title,
            "objective": f"Nhập vai '{user_role}' hoàn thành {len(goals)} mục tiêu trong {timer_ms/1000:.1f}s",
            "scenario": f"Bối cảnh: {loc_name} • Đối thoại cùng {npc_name}",
            "instructions": f"Lắng nghe câu thoại của {npc_name} và nói câu phản xạ tiếng Nhật phù hợp để hoàn thành mục tiêu.",
            "prompt": opening,
            "canonical": canonical,
            "acceptable_variants": variants,
            "translation": opening_vi,
            "situational_data": {
                "category_key": chosen_cat_key,
                "category_label": cat_label,
                "location": loc_name,
                "npc_name": npc_name,
                "npc_personality": npc_personality,
                "npc_opening_dialogue": opening,
                "npc_dialogue_vi": opening_vi,
                "user_role": user_role,
                "goals": goals,
                "unexpected_event": event,
                "useful_phrases": phrases,
                "vocabulary_hints": vocab,
                "is_custom": is_custom,
                "custom_topic": custom_topic if is_custom else None,
            },
            "timer_limit_ms": timer_ms,
            "pressure_level": pressure_level,
            "difficulty": difficulty,
            "constraints": [f"Vai trò: {user_role}", f"Thời gian phản xạ: {timer_ms/1000:.1f}s"],
            "target_patterns": variants[:2],
            "estimated_minutes": duration,
        }
