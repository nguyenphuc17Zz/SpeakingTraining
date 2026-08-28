"""AICurriculumGenerator — 100% dynamic on-the-fly Personalized Curriculum & Roadmap Generation via Gemini AI.

Designs comprehensive 4-stage milestone speaking roadmaps (12-16 lesson nodes) tailored to:
1. Current Level (N5 -> N1)
2. Target Goal (Workplace, Part-time Baito, Daily Life, Travel, JLPT / Kaiwa Exam, Custom)
3. Time Commitment (15m, 30m, 45m, 60m / day)
4. Freeform user wishes (e.g. "Focus on IT client meetings & polite refusal")
"""

from __future__ import annotations

import json
import uuid
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
from app.domains.learning.models import LearningGoal

LEVEL_LABELS = {
    "beginner": "N5 • Sơ cấp 1 (Khởi đầu)",
    "elementary": "N4 • Sơ cấp 2 (Cơ bản)",
    "intermediate": "N3 • Trung cấp (Giao tiếp)",
    "advanced": "N2 • Trung cao cấp (Công sở)",
    "fluent": "N1 • Cao cấp (Thành thạo)",
}

GOAL_LABELS = {
    "workplace": "Công sở & Doanh nghiệp Nhật (ビジネス・仕事)",
    "baito": "Phỏng vấn & Làm thêm Baito (アルバイト・面接)",
    "daily": "Giao tiếp đời sống & Kết bạn (日常会話・友達)",
    "travel": "Du lịch, Định cư & Khẩn cấp (観光・移住・生活)",
    "exam": "Luyện thi Kaiwa & Chứng chỉ JLPT (会話試験・JLPT)",
    "custom": "Mục tiêu tùy biến theo nguyện vọng riêng",
}


class AICurriculumGenerator:
    """Generates dynamic, bespoke 4-stage learning roadmaps tailored to learner profile."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def get_or_generate_user_curriculum(
        self,
        user_id: str,
        level: str = "intermediate",
        target_goal: str = "workplace",
        daily_minutes: int = 30,
        custom_wish: str | None = None,
        force_regenerate: bool = False,
    ) -> dict[str, Any]:
        """Retrieves active user curriculum roadmap or generates a new one via Gemini AI."""
        # 1. Check existing curriculum in database
        stmt = (
            select(LearningGoal)
            .where(LearningGoal.user_id == user_id, LearningGoal.status == "active")
            .order_by(LearningGoal.priority.asc())
        )
        res = await self.db.execute(stmt)
        goals = res.scalars().all()
        curriculum_goal = next(
            (g for g in goals if g.extra_metadata and "curriculum_roadmap" in g.extra_metadata),
            None,
        )

        if curriculum_goal and not force_regenerate:
            roadmap = curriculum_goal.extra_metadata["curriculum_roadmap"]
            return roadmap

        # 2. Generate new roadmap via Gemini AI
        roadmap = await self._generate_ai_roadmap(
            user_id=user_id,
            level=level,
            target_goal=target_goal,
            daily_minutes=daily_minutes,
            custom_wish=custom_wish,
        )

        # 3. Persist into LearningGoal
        if curriculum_goal:
            curriculum_goal.title = roadmap["title"]
            curriculum_goal.description = roadmap["description"]
            curriculum_goal.goal_type = target_goal
            curriculum_goal.extra_metadata = {
                **(curriculum_goal.extra_metadata or {}),
                "curriculum_roadmap": roadmap,
            }
        else:
            new_goal = LearningGoal(
                user_id=user_id,
                title=roadmap["title"],
                description=roadmap["description"],
                goal_type=target_goal,
                priority=1,
                status="active",
                extra_metadata={"curriculum_roadmap": roadmap},
            )
            self.db.add(new_goal)

        await self.db.commit()
        return roadmap

    async def _generate_ai_roadmap(
        self,
        user_id: str,
        level: str,
        target_goal: str,
        daily_minutes: int,
        custom_wish: str | None = None,
    ) -> dict[str, Any]:
        """Calls Gemini AI to design a bespoke 4-stage milestone curriculum."""
        level_name = LEVEL_LABELS.get(level, level)
        goal_name = GOAL_LABELS.get(target_goal, target_goal)
        nonce = uuid.uuid4().hex[:8]

        prompt_text = (
            f"Hãy thiết kế 1 Lộ Trình Học Nói Tiếng Nhật Cá Nhân Hóa (Speaking Curriculum Roadmap) chi tiết, chuẩn sư phạm Nhật Bản. [Nonce: {nonce}]\n"
            f"- Trình độ người học: {level_name}\n"
            f"- Mục tiêu trọng tâm: {goal_name}\n"
            f"- Thời gian học mỗi ngày: {daily_minutes} phút\n"
            f"{f'- Nguyện vọng cụ thể của người học: {custom_wish}' if custom_wish else ''}\n\n"
            f"Yêu cầu lộ trình gồm đúng 4 Chặng Chinh Phục (Milestone Stages), mỗi chặng 3-4 bài học (Nodes), tổng cộng 12-16 bài học:\n"
            f"Chặng 1: Nền móng Âm vị, Cao độ Tokyo & Phản xạ câu đơn.\n"
            f"Chặng 2: Hội thoại đời sống, Tình huống thực tế & Kính ngữ ứng dụng.\n"
            f"Chặng 3: Kính ngữ công sở, Đàm phán chuyên sâu & Xử lý sự cố phức tạp.\n"
            f"Chặng 4: Lưu loát tự nhiên, Triệt tiêu từ đệm & Phỏng vấn thực chiến.\n\n"
            f"Mỗi bài học (Node) PHẢI liên kết trực tiếp với 1 trong 5 phòng luyện của ứng dụng:\n"
            f"- target_mode: '/pitch' (Luyện Cao Độ & Phách)\n"
            f"- target_mode: '/keigo' (Luyện Kính Ngữ Chuyên Sâu)\n"
            f"- target_mode: '/situations' (Luyện Tình Huống Thực Chiến)\n"
            f"- target_mode: '/shadowing' (Luyện Nhại Giọng Bản Xứ)\n"
            f"- target_mode: '/speaking' (Luyện Hội Thoại & Kiểm Soát Từ Đệm Với AI)\n\n"
            f"Trả về duy nhất định dạng JSON:\n"
            f"{{\n"
            f"  \"curriculum_id\": \"curr_{nonce}\",\n"
            f"  \"title\": \"<Tên lộ trình hấp dẫn, VD: Lộ trình Chinh phục Kính ngữ & Đàm phán Công sở N2>\",\n"
            f"  \"description\": \"<Mô tả ngắn gọn giá trị đạt được sau lộ trình>\",\n"
            f"  \"level\": \"{level}\",\n"
            f"  \"level_label\": \"{level_name}\",\n"
            f"  \"target_goal\": \"{target_goal}\",\n"
            f"  \"target_goal_label\": \"{goal_name}\",\n"
            f"  \"daily_minutes\": {daily_minutes},\n"
            f"  \"estimated_weeks\": 8,\n"
            f"  \"total_lessons\": 12,\n"
            f"  \"stages\": [\n"
            f"    {{\n"
            f"      \"stage_number\": 1,\n"
            f"      \"title\": \"Chặng 1: Nền Móng Âm Vị & Phản Xạ Căn Bản\",\n"
            f"      \"badge\": \"Nền Móng\",\n"
            f"      \"color\": \"sky\",\n"
            f"      \"objective\": \"Làm chủ cao độ Tokyo và phản xạ nhanh câu đơn không ngắc ngứ\",\n"
            f"      \"nodes\": [\n"
            f"        {{\n"
            f"          \"id\": \"node_1_1\",\n"
            f"          \"title\": \"<Tên bài học 1>\",\n"
            f"          \"description\": \"<Mô tả ngắn kiến thức>\",\n"
            f"          \"target_mode\": \"/pitch\",\n"
            f"          \"mode_label\": \"Cao Độ & Phách\",\n"
            f"          \"difficulty\": \"N3\",\n"
            f"          \"key_patterns\": [\"Heiban [0]\", \"Atamadaka [1]\"],\n"
            f"          \"estimated_minutes\": 10,\n"
            f"          \"is_completed\": false,\n"
            f"          \"score\": 0\n"
            f"        }}\n"
            f"      ]\n"
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt_text)],
            system_instruction="Bạn là Trưởng ban Đào tạo Phát âm & Hội thoại tiếng Nhật thực chiến. Thiết kế lộ trình logic, chuẩn xác và đúng định dạng JSON.",
            response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT),
            temperature=0.85,
            metadata={"idempotency_key": str(uuid.uuid4())},
        )

        try:
            resp = await self.ai_router.generate(task=AITask.EXERCISE_GENERATION, request=req, user_id=user_id)
            data = json.loads(resp.text.strip())
            return data
        except Exception as e:
            logger.warning(f"[AICurriculumGenerator] AI Generation fallback: {e}")
            return self._build_fallback_curriculum(level, target_goal, daily_minutes, custom_wish)

    def _build_fallback_curriculum(
        self,
        level: str,
        target_goal: str,
        daily_minutes: int,
        custom_wish: str | None = None,
    ) -> dict[str, Any]:
        """Provides an authentic, highly structured 4-stage fallback curriculum."""
        level_name = LEVEL_LABELS.get(level, "N3 • Trung cấp")
        goal_name = GOAL_LABELS.get(target_goal, "Giao tiếp công sở")

        return {
            "curriculum_id": f"curr_fallback_{uuid.uuid4().hex[:6]}",
            "title": f"Lộ Trình Toàn Diện: {goal_name} ({level_name})",
            "description": f"Chương trình rèn luyện 4 chặng nâng cao độ tự nhiên, phản xạ kính ngữ và hội thoại thực chiến trong {daily_minutes} phút/ngày.",
            "level": level,
            "level_label": level_name,
            "target_goal": target_goal,
            "target_goal_label": goal_name,
            "daily_minutes": daily_minutes,
            "estimated_weeks": 8,
            "total_lessons": 12,
            "stages": [
                {
                    "stage_number": 1,
                    "title": "Chặng 1: Nền Móng Âm Vị & Phản Xạ Căn Bản",
                    "badge": "Nền Móng",
                    "color": "sky",
                    "objective": "Làm chủ 4 mô hình cao độ Tokyo, phách trường âm và phản xạ câu đơn",
                    "nodes": [
                        {
                            "id": "node_1_1",
                            "title": "Phân biệt Cặp từ tối thiểu & Cao độ Tokyo (雨 vs 飴)",
                            "description": "Luyện tai nghe và hạ giọng đúng âm tiết chuẩn giọng Tokyo",
                            "target_mode": "/pitch",
                            "mode_label": "Cao Độ & Phách",
                            "difficulty": "N3",
                            "key_patterns": ["平板型 [0]", "頭高型 [1]"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_1_2",
                            "title": "Độ dài phách Mora & Vô thanh hóa nguyên âm i/u",
                            "description": "Tránh phát âm nuốt phách trường âm và nuốt thanh tự nhiên",
                            "target_mode": "/pitch",
                            "mode_label": "Cao Độ & Phách",
                            "difficulty": "N3",
                            "key_patterns": ["拍の長さ", "母音無声化"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_1_3",
                            "title": "Phản xạ câu đơn 3 giây tại Cửa hàng tiện lợi Konbini",
                            "description": "Từ chối túi nilon, hâm nóng bento và thanh toán thẻ Suica",
                            "target_mode": "/situations",
                            "mode_label": "Tình Huống Thực Chiến",
                            "difficulty": "N3",
                            "key_patterns": ["袋は結構です", "温めお願いします"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                    ],
                },
                {
                    "stage_number": 2,
                    "title": "Chặng 2: Hội Thoại Đời Sống & Kính Ngữ Ứng Dụng",
                    "badge": "Ứng Dụng",
                    "color": "emerald",
                    "objective": "Giao tiếp tự nhiên, xử lý các tình huống nhà ga, quán ăn và đổi hàng",
                    "nodes": [
                        {
                            "id": "node_2_1",
                            "title": "Kính ngữ cơ bản trong giao tiếp xã giao (Teineigo & Lịch sự)",
                            "description": "Duy trì đuôi câu Desu/Masu nhất quán và cách dùng từ đệm lịch sự",
                            "target_mode": "/keigo",
                            "mode_label": "Kính Ngữ",
                            "difficulty": "N3",
                            "key_patterns": ["丁寧語", "クッション言葉"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_2_2",
                            "title": "Xử lý tình huống mua vé Shinkansen & Đổi hàng do lỗi",
                            "description": "Đặt vé ghế chỉ định Shiteiseki và thương lượng đổi món/hàng",
                            "target_mode": "/situations",
                            "mode_label": "Tình Huống Thực Chiến",
                            "difficulty": "N3",
                            "key_patterns": ["指定席", "交換していただけますか"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_2_3",
                            "title": "Shadowing nhại giọng đoạn hội thoại người Nhật 1.0x",
                            "description": "Luyện nhịp điệu và ngữ điệu tự nhiên như người bản xứ",
                            "target_mode": "/shadowing",
                            "mode_label": "Shadowing",
                            "difficulty": "N3",
                            "key_patterns": ["Intonation", "Speed 1.0x"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                    ],
                },
                {
                    "stage_number": 3,
                    "title": "Chặng 3: Kính Ngữ Công Sở & Đàm Phán Chuyên Nghiệp",
                    "badge": "Chuyên Sâu",
                    "color": "purple",
                    "objective": "Thành thạo Tôn kính ngữ, Khiêm nhường ngữ và văn hóa Uchi/Soto",
                    "nodes": [
                        {
                            "id": "node_3_1",
                            "title": "25 Động từ bất quy tắc Tôn kính ngữ (Sonkeigo) & Khiêm nhường ngữ",
                            "description": "Phân biệt tuyệt đối người mình Uchi vs người ngoài Soto",
                            "target_mode": "/keigo",
                            "mode_label": "Kính Ngữ",
                            "difficulty": "N2",
                            "key_patterns": ["おっしゃる/申す", "いらっしゃる/参る"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_3_2",
                            "title": "Trao đổi danh thiếp Meishi Koukan & Báo cáo tiến độ Hou-Ren-So",
                            "description": "Nghi thức chào hỏi đối tác và báo cáo công việc ngắn gọn logic",
                            "target_mode": "/situations",
                            "mode_label": "Tình Huống Thực Chiến",
                            "difficulty": "N2",
                            "key_patterns": ["名刺交換", "報連相 (進捗報告)"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_3_3",
                            "title": "Từ chối khéo léo và nói giảm nói tránh (〜わけではない / 〜ですが)",
                            "description": "Tránh xung đột trực diện và giải thích lý do mềm mỏng",
                            "target_mode": "/speaking",
                            "mode_label": "Hội Thoại AI",
                            "difficulty": "N2",
                            "key_patterns": ["〜わけではない", "〜恐れ入りますが"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                    ],
                },
                {
                    "stage_number": 4,
                    "title": "Chặng 4: Lưu Loát Tự Nhiên & Phỏng Vấn Thực Chiến",
                    "badge": "Thực Chiến",
                    "color": "amber",
                    "objective": "Triệt tiêu từ đệm ano/etto, phản xạ tức thì dưới 1.5s và phỏng vấn tự tin",
                    "nodes": [
                        {
                            "id": "node_4_1",
                            "title": "Kiểm soát từ đệm (ano, etto) & Tạo khoảng lặng tự nhiên",
                            "description": "Thay thế từ đệm vô nghĩa bằng từ nối tư duy logic",
                            "target_mode": "/speaking",
                            "mode_label": "Hội Thoại AI",
                            "difficulty": "N2",
                            "key_patterns": ["Filler Control", "Natural Pause"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_4_2",
                            "title": "Nhập vai phỏng vấn xin việc & Đàm phán điều kiện làm việc",
                            "description": "Trả lời câu hỏi tình huống và thể hiện năng lực tự tin",
                            "target_mode": "/situations",
                            "mode_label": "Tình Huống Thực Chiến",
                            "difficulty": "N2",
                            "key_patterns": ["面接応答", "自己PR"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                        {
                            "id": "node_4_3",
                            "title": "Đánh giá Năng lực Tổng Thể & Thử thách Boss Chiến",
                            "description": "Kiểm tra toàn diện 4 trụ cột: Cao độ, Kính ngữ, Tình huống và Độ trôi chảy",
                            "target_mode": "/bosses",
                            "mode_label": "Thử Thách Boss",
                            "difficulty": "N2",
                            "key_patterns": ["総合評価", "Boss Challenge"],
                            "estimated_minutes": 10,
                            "is_completed": False,
                            "score": 0,
                        },
                    ],
                },
            ],
        }

    async def toggle_node_completion(
        self,
        user_id: str,
        node_id: str,
        is_completed: bool | None = None,
        score: float | None = None,
    ) -> dict[str, Any] | None:
        """Toggles or updates the completion status and score of a specific lesson node."""
        stmt = (
            select(LearningGoal)
            .where(LearningGoal.user_id == user_id, LearningGoal.status == "active")
            .order_by(LearningGoal.priority.asc())
        )
        res = await self.db.execute(stmt)
        curriculum_goal = next(
            (g for g in res.scalars().all() if g.extra_metadata and "curriculum_roadmap" in g.extra_metadata),
            None,
        )
        if not curriculum_goal:
            return None

        roadmap = curriculum_goal.extra_metadata["curriculum_roadmap"]
        node_found = False

        for stage in roadmap.get("stages", []):
            for node in stage.get("nodes", []):
                if node["id"] == node_id:
                    node_found = True
                    if is_completed is not None:
                        node["is_completed"] = is_completed
                    else:
                        node["is_completed"] = not node.get("is_completed", False)
                    if score is not None:
                        node["score"] = score
                    break
            if node_found:
                break

        if node_found:
            curriculum_goal.extra_metadata = {
                **curriculum_goal.extra_metadata,
                "curriculum_roadmap": roadmap,
            }
            await self.db.commit()

        return roadmap
