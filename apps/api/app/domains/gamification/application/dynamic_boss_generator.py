import json
import random
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.gamification.models import BossDefinition


SAMPLE_BOSS_PROMPTS = [
    {"topic": "Thương Lượng Tăng Lương Với Trưởng Phòng Nhật", "difficulty": "hard", "level": 5},
    {"topic": "Báo Cáo Sự Cố Rò Rỉ Dữ Liệu Khẩn Cấp Nửa Đêm Cho Giám Đốc", "difficulty": "extreme", "level": 10},
    {"topic": "Thuyết Trình Đề Xuất Dự Án Mới Trước Hội Đồng Cổ Đông", "difficulty": "hard", "level": 7},
    {"topic": "Giải Trình Với Hải Quan Sân Bay Narita Về Hành Lý Bị Giữ", "difficulty": "normal", "level": 3},
    {"topic": "Xin Gia Hạn Deadline Hợp Đồng Với Đối Tác Khó Tính", "difficulty": "hard", "level": 6},
    {"topic": "Xoa Dịu Khách Hàng VIP Đòi Hủy Đơn Hàng Do Giao Chậm", "difficulty": "extreme", "level": 12},
    {"topic": "Phỏng Vấn Vòng Cuối Giám Đốc Nhân Sự Tập Đoàn Đa Quốc Gia", "difficulty": "extreme", "level": 15},
    {"topic": "Thuyết Phục Đồng Nghiệp Tiền Bối Hỗ Trợ Đề Án Bị Phản Đối", "difficulty": "normal", "level": 4},
    {"topic": "Giải Trình Với Cảnh Sát Đồn Koban Khi Bị Mất Toàn Bộ Hộ Chiếu & Giấy Tờ", "difficulty": "normal", "level": 3},
    {"topic": "Đàm Phán Thuê Nhà Chung Cư Tại Shibuya Trước Chủ Nhà Kỹ Tính", "difficulty": "normal", "level": 4},
    {"topic": "Xử Lý Sự Cố Khách Hàng Dị Ứng Thực Phẩm Tại Nhà Hàng Cao Cấp Ginza", "difficulty": "hard", "level": 8},
    {"topic": "Họp Báo Trả Lời Phỏng Vấn Truyền Thông Khi Sản Phẩm Bị Thu Hồi", "difficulty": "extreme", "level": 14},
    {"topic": "Đàm Phán Mua Lại Bản Quyền Độc Quyền Với Tác Giả Nhật Bản", "difficulty": "hard", "level": 9},
    {"topic": "Thương Thảo Giảm 15% Chi Phí Sản Xuất Với Nhà Cung Ứng Khó Tính", "difficulty": "hard", "level": 8},
    {"topic": "Xin Lỗi Khách Hàng Doanh Nghiệp Vì Hệ Thống Ngân Hàng Ngừng Hoạt Động", "difficulty": "extreme", "level": 13},
    {"topic": "Thuyết Phục Ban Giám Khảo Cấp Học Bổng Toàn Phần MEXT", "difficulty": "hard", "level": 7},
]

_BOSS_PROMPTS_QUEUE: list[dict[str, Any]] = []


def _get_next_boss_prompt() -> dict[str, Any]:
    global _BOSS_PROMPTS_QUEUE
    if not _BOSS_PROMPTS_QUEUE:
        _BOSS_PROMPTS_QUEUE = random.sample(SAMPLE_BOSS_PROMPTS, len(SAMPLE_BOSS_PROMPTS))
    return _BOSS_PROMPTS_QUEUE.pop(0)


class DynamicBossGenerator:
    """Generates infinite high-stakes Japanese speaking boss battle trials using Gemini AI."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def generate_boss(
        self,
        topic: str | None = None,
        difficulty: str = "normal",
        required_level: int = 3,
        user_id: str | None = None,
    ) -> BossDefinition:
        """Dynamically designs and persists a new high-stakes Boss challenge."""
        if not topic or topic.strip() == "" or topic == "random":
            chosen = _get_next_boss_prompt()
            topic = chosen["topic"]
            difficulty = chosen["difficulty"]
            required_level = chosen["level"]

        prompt = f"""Bạn là Đạo diễn Thiết Kế Đấu Trường Luyện Nói Tiếng Nhật (Dojo Boss Arena Director).
Hãy thiết kế một Thử Thách Boss Đối Kháng Áp Lực Cao (High-Stakes Speaking Boss Trial) theo chủ đề:
Chủ đề: {topic}
Độ khó: {difficulty} (normal, hard, extreme)
Cấp độ yêu cầu: Level {required_level}

Yêu cầu xuất ra định dạng JSON thuần túy (không markdown, không ```json):
{{
  "name": "Tên Boss và chức danh bằng tiếng Nhật kèm Hán tự (ví dụ: 鬼の取締役・田中 (Trưởng ban Tanaka nghiêm khắc))",
  "subtitle": "Phụ đề tóm tắt bối cảnh bằng tiếng Việt (ngắn gọn, kịch tính)",
  "description": "Mô tả chi tiết tình huống đối thoại áp lực và thái độ của Boss",
  "persona_key": "system_default_persona",
  "difficulty": "{difficulty}",
  "required_level": {required_level},
  "pass_score_threshold": {75.0 if difficulty == "normal" else 82.0 if difficulty == "hard" else 88.0},
  "xp_reward": {500 if difficulty == "normal" else 900 if difficulty == "hard" else 1500},
  "title_reward": "Danh hiệu độc quyền khi chiến thắng kèm tiếng Nhật (ví dụ: 交渉の達人 (Bậc Thầy Đàm Phán))",
  "objectives": [
    "Mục tiêu 1 bằng tiếng Việt (ví dụ: Sử dụng chuẩn xác Kính ngữ Sonkeigo/Kenjougo)",
    "Mục tiêu 2 bằng tiếng Việt (ví dụ: Trình bày lý do mạch lạc dưới 15 giây)",
    "Mục tiêu 3 bằng tiếng Việt (ví dụ: Đưa ra giải pháp thuyết phục không lúng túng)"
  ],
  "scenario_template": "Bối cảnh mở đầu chi tiết",
  "initial_boss_line_ja": "Câu mở đầu đầy áp lực của Boss bằng tiếng Nhật (kèm kanji)",
  "initial_boss_line_vi": "Dịch nghĩa câu mở đầu của Boss sang tiếng Việt"
}}"""

        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
            system_instruction="Bạn là AI Game Master thiết kế màn chơi Boss Đấu Trường tiếng Nhật. Luôn trả về đúng chuẩn JSON.",
            temperature=0.7,
        )

        boss_data = None
        try:
            resp = await self.ai_router.generate(task=AITask.EXERCISE_GENERATION, request=req, user_id=user_id)
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            boss_data = json.loads(raw.strip())
        except Exception as e:
            logger.warning(f"[DynamicBossGenerator] Gemini generation fallback: {e}")
            boss_data = {
                "name": f"試練の相手・{topic[:15]}",
                "subtitle": f"Thử thách đối thoại: {topic}",
                "description": f"Vượt qua buổi đối thoại căng thẳng về chủ đề '{topic}' với người Nhật có chuyên môn cao.",
                "persona_key": "system_default_persona",
                "difficulty": difficulty,
                "required_level": required_level,
                "pass_score_threshold": 75.0 if difficulty == "normal" else 85.0,
                "xp_reward": 600 if difficulty == "normal" else 1000,
                "title_reward": f"Chinh Phục {topic[:10]}",
                "objectives": [
                    "Sử dụng Kính ngữ phù hợp hoàn cảnh",
                    "Phản xạ câu nói tự tin dưới 3 giây",
                    "Giữ nhịp điệu phát âm chuẩn Tokyo",
                ],
                "scenario_template": f"Bạn đang tham gia buổi đàm phán quan trọng về: {topic}.",
                "initial_boss_line_ja": "本日はお時間をいただき感謝いたします。早速ですが、今回の件についてご説明いただけますか。",
                "initial_boss_line_vi": "Cảm ơn bạn đã dành thời gian hôm nay. Không để mất thời gian, bạn có thể giải thích rõ về sự việc lần này không?",
            }

        unique_key = f"boss_{uuid.uuid4().hex[:8]}"
        boss = BossDefinition(
            key=unique_key,
            name=boss_data.get("name", f"Boss: {topic}"),
            subtitle=boss_data.get("subtitle", "Thử thách đối kháng cao độ"),
            description=boss_data.get("description", "Thử thách đối thoại áp lực"),
            persona_key="system_default_persona",
            difficulty=boss_data.get("difficulty", difficulty),
            required_level=int(boss_data.get("required_level", required_level)),
            pass_score_threshold=float(boss_data.get("pass_score_threshold", 75.0)),
            xp_reward=int(boss_data.get("xp_reward", 600)),
            title_reward=boss_data.get("title_reward", "Võ Sĩ Đạo Trường"),
            objectives_json=boss_data.get("objectives", []),
            scenario_template=boss_data.get("scenario_template", topic),
            prompt_modifier=f"InitialLineJa: {boss_data.get('initial_boss_line_ja', '')} | InitialLineVi: {boss_data.get('initial_boss_line_vi', '')}",
        )
        self.db.add(boss)
        await self.db.commit()
        await self.db.refresh(boss)

        logger.info(f"[DynamicBossGenerator] Successfully generated Boss '{boss.name}' ({boss.key})")
        return boss
